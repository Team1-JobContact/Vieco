"""Đơn ứng tuyển (PB-019, PB-020, PB-022): nộp đơn, theo dõi, rút đơn, xử lý và lịch sử trạng thái."""
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from src.models.catalog import Province
from src.models.company import Company, CompanyMember
from src.models.engagement import Notification
from src.models.profile import CV, CandidateProfile
from src.models.recruitment import Application, ApplicationStatusHistory, Job
from src.models.user import User
from src.services import candidate_service, company_service, cv_service
from src.services.auth_service import _utcnow
from src.services.public_service import public_jobs_query

TRANSITIONS = {"NEW": {"VIEWED", "INTERVIEW", "REJECTED"}, "VIEWED": {"INTERVIEW", "REJECTED"},
               "INTERVIEW": {"ACCEPTED", "REJECTED"}}
STATUS_LABELS = {"NEW": "Đã gửi", "VIEWED": "Đang xem xét", "INTERVIEW": "Mời phỏng vấn",
                 "ACCEPTED": "Trúng tuyển", "REJECTED": "Chưa phù hợp", "WITHDRAWN": "Đã rút"}
BASE_KEYS = ("id", "job_id", "candidate_profile_id", "cv_id", "cover_letter", "status",
             "withdrawn_at", "created_at", "updated_at")


def fields(row):
    return {key: getattr(row, key) for key in BASE_KEYS}


def enrich(db, row):
    """Thêm thông tin hiển thị: tin, công ty, CV và ứng viên (chỉ trả cho chủ đơn hoặc công ty nhận đơn)."""
    data = fields(row)
    job = db.get(Job, row.job_id)
    company = db.get(Company, job.company_id) if job else None
    province = db.get(Province, job.province_id) if job and job.province_id else None
    cv = db.get(CV, row.cv_id)
    profile = db.get(CandidateProfile, row.candidate_profile_id)
    user = db.get(User, profile.user_id) if profile else None
    data.update(
        job_title=job.title if job else None,
        job_status=job.status if job else None,
        company_id=company.id if company else None,
        company_name=company.name if company else None,
        company_logo_url=company.logo_url if company else None,
        province_name=province.name if province else None,
        cv_file_name=cv.file_name if cv else None,
        candidate_name=user.full_name if user else None,
        candidate_email=user.email if user else None,
        candidate_phone=user.phone if user else None,
        candidate_headline=profile.headline if profile else None,
    )
    return data


def history(db, row, user, old, note=None):
    db.add(ApplicationStatusHistory(application_id=row.id, from_status=old, to_status=row.status,
                                    changed_by=user.id, note=note))


def create_application(db, user, data):
    profile = candidate_service.get_profile_or_404(db, user)
    job = public_jobs_query(db).filter(Job.id == data.job_id).with_for_update().first()
    if job is None:
        raise HTTPException(409, "Tin không còn nhận ứng tuyển")
    cv = db.query(CV).filter(CV.id == data.cv_id, CV.candidate_profile_id == profile.id,
                             CV.deleted_at.is_(None)).first()
    if cv is None:
        raise HTTPException(404, "Không tìm thấy CV của bạn")
    row = Application(job_id=job.id, candidate_profile_id=profile.id, cv_id=cv.id,
                      cover_letter=data.cover_letter, status="NEW")
    db.add(row)
    try:
        db.flush()
        history(db, row, user, None)
        for (uid,) in db.query(CompanyMember.user_id).filter(CompanyMember.company_id == job.company_id):
            db.add(Notification(user_id=uid, type="APPLICATION_NEW", title="Đơn ứng tuyển mới",
                                message=f"Tin {job.title} có đơn ứng tuyển mới từ {user.full_name}",
                                action_url=f"/pages/employer-jobs.html?job_id={job.id}",
                                reference_type="APPLICATION", reference_id=row.id))
        db.commit()
        from src.services.notification_service import send_for_reference
        send_for_reference(db, "APPLICATION", row.id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bạn đã ứng tuyển tin này")
    return enrich(db, row)


def paginate(db, query, status, page, page_size):
    if status:
        query = query.filter(Application.status == status)
    total = query.count()
    rows = (query.order_by(Application.created_at.desc(), Application.id.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return dict(items=[enrich(db, r) for r in rows], total=total, page=page, page_size=page_size)


def my_applications(db, user, page, page_size, status=None):
    profile = candidate_service.find_profile(db, user)
    if profile is None:
        return dict(items=[], total=0, page=page, page_size=page_size)
    return paginate(db, db.query(Application).filter(Application.candidate_profile_id == profile.id),
                    status, page, page_size)


def employer_applications(db, user, job_id, page, page_size, status=None):
    company, _ = company_service.get_membership_or_404(db, user)
    if not db.query(Job.id).filter(Job.id == job_id, Job.company_id == company.id).first():
        raise HTTPException(404, "Không tìm thấy tin của công ty bạn")
    return paginate(db, db.query(Application).filter(Application.job_id == job_id), status, page, page_size)


def _get_accessible(db, user, application_id):
    """BR-08/BR-16: chỉ chủ đơn hoặc thành viên công ty nhận đơn được xem đơn và CV."""
    row = None
    if user.role_name == "CANDIDATE":
        profile = candidate_service.find_profile(db, user)
        if profile is not None:
            row = db.query(Application).filter(Application.id == application_id,
                                               Application.candidate_profile_id == profile.id).first()
    elif user.role_name == "EMPLOYER":
        membership = company_service.find_membership(db, user)
        if membership is not None:
            row = (db.query(Application).join(Job, Job.id == Application.job_id)
                   .filter(Application.id == application_id, Job.company_id == membership[0].id).first())
    if row is None:
        raise HTTPException(404, "Không tìm thấy đơn ứng tuyển")
    return row


def get_application(db, user, application_id):
    row = _get_accessible(db, user, application_id)
    data = enrich(db, row)
    profile = db.get(CandidateProfile, row.candidate_profile_id)
    province = db.get(Province, profile.province_id) if profile and profile.province_id else None
    data["candidate_profile"] = dict(
        date_of_birth=profile.date_of_birth, gender=profile.gender, address=profile.address,
        province_name=province.name if province else None, summary=profile.summary,
    ) if profile else None
    rows = (db.query(ApplicationStatusHistory, User.full_name)
            .outerjoin(User, User.id == ApplicationStatusHistory.changed_by)
            .filter(ApplicationStatusHistory.application_id == row.id)
            .order_by(ApplicationStatusHistory.created_at, ApplicationStatusHistory.id).all())
    data["history"] = [dict(from_status=h.from_status, to_status=h.to_status, note=h.note,
                            changed_by_name=name, created_at=h.created_at) for h, name in rows]
    data["allowed_statuses"] = sorted(TRANSITIONS.get(row.status, set())) if user.role_name == "EMPLOYER" else []
    data["can_withdraw"] = user.role_name == "CANDIDATE" and row.status in ("NEW", "VIEWED")
    return data


def application_cv(db, user, application_id):
    """Tải CV đã nộp kèm đơn, kể cả khi ứng viên đã xóa mềm CV đó khỏi hồ sơ (BR-15)."""
    row = _get_accessible(db, user, application_id)
    cv = db.get(CV, row.cv_id)
    if cv is None:
        raise HTTPException(404, "Không tìm thấy CV")
    path, media_type = cv_service.file_for_download(cv)
    return path, media_type, cv.file_name


def withdraw(db, user, application_id):
    profile = candidate_service.get_profile_or_404(db, user)
    row = db.query(Application).filter(Application.id == application_id,
                                       Application.candidate_profile_id == profile.id).with_for_update().first()
    if row is None:
        raise HTTPException(404, "Không tìm thấy đơn ứng tuyển")
    if row.status not in ("NEW", "VIEWED"):
        raise HTTPException(409, "Chỉ rút đơn khi chưa phỏng vấn hoặc có kết quả")
    old = row.status
    row.status = "WITHDRAWN"
    row.withdrawn_at = _utcnow()
    history(db, row, user, old)
    db.commit()
    return enrich(db, row)


def update_status(db, user, application_id, data):
    company, _ = company_service.get_membership_or_404(db, user)
    row = (db.query(Application).join(Job, Job.id == Application.job_id)
           .filter(Application.id == application_id, Job.company_id == company.id).with_for_update().first())
    if row is None:
        raise HTTPException(404, "Không tìm thấy đơn của công ty bạn")
    if data.status not in TRANSITIONS.get(row.status, set()):
        raise HTTPException(409, "Chuyển trạng thái đơn không hợp lệ")
    old = row.status
    row.status = data.status
    history(db, row, user, old, data.note)
    profile = db.get(CandidateProfile, row.candidate_profile_id)
    job = db.get(Job, row.job_id)
    db.add(Notification(user_id=profile.user_id, type="APPLICATION_STATUS", title="Cập nhật đơn ứng tuyển",
                        message=f"Đơn ứng tuyển vị trí {job.title} chuyển sang trạng thái: "
                                f"{STATUS_LABELS[data.status]}",
                        action_url="/pages/profile.html#applications",
                        reference_type="APPLICATION", reference_id=row.id))
    db.commit()
    from src.services.notification_service import send_for_reference
    send_for_reference(db, "APPLICATION", row.id)
    return enrich(db, row)
