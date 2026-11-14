from datetime import date, datetime, timezone
import math

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)

from src.models.catalog import Industry, Province, Skill
from src.models.company import Company, CompanyMember
from src.models.engagement import AuditLog, Notification
from src.models.recruitment import Job, JobSkill
from src.models.user import User
from src.schemas.job import (
    JobCreate, JobExtendRequest, JobListResponse, JobResponse, JobUpdate, SkillItem,
)
from src.services.company_service import find_membership


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def require_approved_company(db: Session, user: User) -> tuple[Company, CompanyMember]:
    """Kiểm tra điều kiện tiên quyết: tài khoản NTD phải thuộc công ty đã được Admin duyệt (BR-02, BR-12)."""
    row = find_membership(db, user)
    if row is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Bạn chưa thuộc công ty nào. Vui lòng tạo hồ sơ công ty trước.",
        )
    company, member = row
    if company.status != "APPROVED":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Công ty của bạn chưa được Admin duyệt. Không thể thực hiện thao tác quản lý tin tuyển dụng.",
        )
    return company, member


def _check_catalog(db: Session, industry_id: int | None, province_id: int | None,
                   skill_ids: list[int] | None = None) -> None:
    if industry_id is not None:
        ind = db.query(Industry).filter(Industry.id == industry_id, Industry.is_active.is_(True)).first()
        if ind is None:
            raise HTTPException(HTTP_422, "Ngành nghề không tồn tại hoặc đã bị ẩn")
    if province_id is not None:
        prov = db.query(Province).filter(Province.id == province_id, Province.is_active.is_(True)).first()
        if prov is None:
            raise HTTPException(HTTP_422, "Tỉnh/thành không tồn tại hoặc đã bị ẩn")
    if skill_ids:
        unique_ids = list(set(skill_ids))
        count = db.query(Skill).filter(Skill.id.in_(unique_ids), Skill.is_active.is_(True)).count()
        if count != len(unique_ids):
            raise HTTPException(HTTP_422,
                                "Một hoặc nhiều kỹ năng không tồn tại hoặc đã bị ẩn")


def _validate_job_submission(title: str | None, industry_id: int | None, province_id: int | None,
                            description: str | None, requirements: str | None,
                            employment_type: str | None, experience_level: str | None,
                            deadline: date | None, salary_min: int | None, salary_max: int | None,
                            positions: int | None) -> None:
    """Kiểm tra các trường bắt buộc khi gửi duyệt theo SRS mục 3.6 và FR-M2-01."""
    if not title or len(title.strip()) < 5:
        raise HTTPException(HTTP_422, "Tiêu đề tin tuyển dụng phải từ 5 ký tự trở lên")
    if not industry_id:
        raise HTTPException(HTTP_422, "Ngành nghề là bắt buộc khi gửi duyệt tin")
    if not province_id:
        raise HTTPException(HTTP_422, "Địa điểm làm việc (Tỉnh/thành) là bắt buộc khi gửi duyệt")
    if not description or len(description.strip()) < 10:
        raise HTTPException(HTTP_422, "Mô tả công việc là bắt buộc (tối thiểu 10 ký tự)")
    if not requirements or len(requirements.strip()) < 10:
        raise HTTPException(HTTP_422, "Yêu cầu công việc là bắt buộc (tối thiểu 10 ký tự)")
    if not employment_type:
        raise HTTPException(HTTP_422, "Hình thức làm việc là bắt buộc khi gửi duyệt tin")
    if not experience_level:
        raise HTTPException(HTTP_422, "Yêu cầu kinh nghiệm là bắt buộc khi gửi duyệt tin")
    if not deadline:
        raise HTTPException(HTTP_422, "Hạn nộp hồ sơ là bắt buộc khi gửi duyệt tin")
    if deadline < date.today():
        raise HTTPException(HTTP_422, "Hạn nộp hồ sơ phải là ngày hiện tại hoặc tương lai")
    if positions is not None and positions < 1:
        raise HTTPException(HTTP_422, "Số lượng tuyển phải lớn hơn hoặc bằng 1")
    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        raise HTTPException(HTTP_422,
                            "Mức lương tối thiểu không được lớn hơn mức lương tối đa")


def _audit(db: Session, user: User, action: str, job: Job, old: dict, new: dict) -> None:
    db.add(AuditLog(user_id=user.id, action=action, entity_type="JOB",
                    entity_id=job.id, old_values=old, new_values=new))


def _notify_employer(db: Session, user_id: int, job: Job, type_: str, title: str, message: str) -> None:
    db.add(Notification(
        user_id=user_id,
        type=type_,
        title=title,
        message=message,
        action_url=f"/employer/jobs/{job.id}",
        reference_type="JOB",
        reference_id=job.id,
    ))


def to_job_response(db: Session, job: Job) -> JobResponse:
    company = db.query(Company).filter(Company.id == job.company_id).first()
    industry = db.query(Industry).filter(Industry.id == job.industry_id).first() if job.industry_id else None
    province = db.query(Province).filter(Province.id == job.province_id).first() if job.province_id else None

    # Lấy danh sách kỹ năng
    skills_query = (
        db.query(Skill.id, Skill.name)
        .join(JobSkill, JobSkill.skill_id == Skill.id)
        .filter(JobSkill.job_id == job.id)
        .all()
    )
    skills = [SkillItem(id=s[0], name=s[1]) for s in skills_query]

    return JobResponse(
        id=job.id,
        company_id=job.company_id,
        company_name=company.name if company else None,
        created_by=job.created_by,
        title=job.title,
        industry_id=job.industry_id,
        industry_name=industry.name if industry else None,
        province_id=job.province_id,
        province_name=province.name if province else None,
        work_address=job.work_address,
        description=job.description,
        requirements=job.requirements,
        benefits=job.benefits,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        experience_level=job.experience_level,
        employment_type=job.employment_type,
        positions=job.positions,
        deadline=job.deadline,
        status=job.status,
        reject_reason=job.reject_reason,
        reviewed_by=job.reviewed_by,
        reviewed_at=job.reviewed_at,
        published_at=job.published_at,
        closed_at=job.closed_at,
        removed_by=job.removed_by,
        removed_at=job.removed_at,
        removal_reason=job.removal_reason,
        view_count=job.view_count,
        created_at=job.created_at,
        updated_at=job.updated_at,
        skills=skills,
    )


# ---------- Nhà tuyển dụng ----------

def get_employer_job_or_404(db: Session, job_id: int, company_id: int) -> Job:
    """Lấy tin theo ID và xác thực thuộc công ty của nhà tuyển dụng (BR-13)."""
    job = db.query(Job).filter(Job.id == job_id, Job.company_id == company_id).first()
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tin tuyển dụng trong công ty của bạn")
    return job


def create_job(db: Session, user: User, data: JobCreate) -> JobResponse:
    company, _ = require_approved_company(db, user)
    _check_catalog(db, data.industry_id, data.province_id, data.skill_ids)

    if data.salary_min is not None and data.salary_max is not None and data.salary_min > data.salary_max:
        raise HTTPException(HTTP_422,
                            "Mức lương tối thiểu không được lớn hơn mức lương tối đa")

    if data.action == "submit":
        _validate_job_submission(
            data.title, data.industry_id, data.province_id, data.description,
            data.requirements, data.employment_type, data.experience_level,
            data.deadline, data.salary_min, data.salary_max, data.positions,
        )
        initial_status = "PENDING"
    else:
        initial_status = "DRAFT"

    job = Job(
        company_id=company.id,
        created_by=user.id,
        title=data.title,
        industry_id=data.industry_id,
        province_id=data.province_id,
        work_address=data.work_address,
        description=data.description,
        requirements=data.requirements,
        benefits=data.benefits,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        salary_currency=data.salary_currency or "VND",
        experience_level=data.experience_level,
        employment_type=data.employment_type,
        positions=data.positions or 1,
        deadline=data.deadline,
        status=initial_status,
    )
    db.add(job)
    db.flush()

    if data.skill_ids:
        for sid in set(data.skill_ids):
            db.add(JobSkill(job_id=job.id, skill_id=sid))

    _audit(db, user, "CREATE_JOB", job, {}, {"title": job.title, "status": job.status})
    db.commit()
    db.refresh(job)
    return to_job_response(db, job)


def list_employer_jobs(
    db: Session,
    user: User,
    status_filter: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> JobListResponse:
    company, _ = require_approved_company(db, user)
    query = db.query(Job).filter(Job.company_id == company.id)

    if status_filter:
        query = query.filter(Job.status == status_filter)
    if q and q.strip():
        query = query.filter(Job.title.ilike(f"%{q.strip()}%"))

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    items = (
        query.order_by(Job.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return JobListResponse(
        items=[to_job_response(db, j) for j in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def get_employer_job(db: Session, user: User, job_id: int) -> JobResponse:
    company, _ = require_approved_company(db, user)
    job = get_employer_job_or_404(db, job_id, company.id)
    return to_job_response(db, job)


def update_job(db: Session, user: User, job_id: int, data: JobUpdate) -> JobResponse:
    company, _ = require_approved_company(db, user)
    job = get_employer_job_or_404(db, job_id, company.id)

    _check_catalog(db, data.industry_id, data.province_id, data.skill_ids)

    old_values = {
        "title": job.title,
        "status": job.status,
        "description": job.description,
        "requirements": job.requirements,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "deadline": str(job.deadline) if job.deadline else None,
    }

    # PATCH: omitted fields stay unchanged; explicit null clears optional values.
    changes = data.model_dump(exclude_unset=True)
    for field in ("title", "positions", "salary_currency"):
        if field in changes and changes[field] is None:
            raise HTTPException(HTTP_422, f"Trường {field} không được để trống")
    new_smin = changes.get("salary_min", job.salary_min)
    new_smax = changes.get("salary_max", job.salary_max)
    if new_smin is not None and new_smax is not None and new_smin > new_smax:
        raise HTTPException(HTTP_422,
                            "Mức lương tối thiểu không được lớn hơn mức lương tối đa")

    # Kiểm tra xem có chỉnh sửa nội dung chính không (FR-M2-03)
    major_fields = [
        "title", "industry_id", "province_id", "work_address", "description",
        "requirements", "benefits", "salary_min", "salary_max", "salary_currency",
        "experience_level", "employment_type", "positions", "deadline",
    ]
    is_major_edited = False
    for field in major_fields:
        if field not in changes:
            continue
        val = changes[field]
        if val != getattr(job, field):
            is_major_edited = True
            setattr(job, field, val)

    if "skill_ids" in changes:
        current_skills = {s[0] for s in db.query(JobSkill.skill_id).filter(JobSkill.job_id == job.id).all()}
        new_skills = set(data.skill_ids)
        if current_skills != new_skills:
            is_major_edited = True
            db.query(JobSkill).filter(JobSkill.job_id == job.id).delete()
            for sid in new_skills:
                db.add(JobSkill(job_id=job.id, skill_id=sid))

    # FR-M2-03: Tin đã duyệt khi sửa nội dung chính cần duyệt lại
    status_changed_to_pending = False
    if job.status == "APPROVED" and is_major_edited:
        job.status = "PENDING"
        job.published_at = None
        status_changed_to_pending = True
        _notify_employer(
            db, user.id, job, "JOB_STATUS_CHANGED",
            "Tin tuyển dụng chuyển sang chờ duyệt lại",
            f"Tin tuyển dụng '{job.title}' đã được chuyển sang trạng thái Chờ duyệt lại do bạn vừa chỉnh sửa nội dung chính.",
        )

    _audit(
        db, user, "UPDATE_JOB", job, old_values,
        {"title": job.title, "status": job.status, "major_edited": is_major_edited},
    )
    db.commit()
    db.refresh(job)
    return to_job_response(db, job)


def submit_job(db: Session, user: User, job_id: int) -> JobResponse:
    """Gửi duyệt tin nháp hoặc tin bị từ chối (DRAFT/REJECTED -> PENDING) (FR-M2-01, FR-M2-02, BR-14)."""
    company, _ = require_approved_company(db, user)
    job = get_employer_job_or_404(db, job_id, company.id)

    if job.status not in ("DRAFT", "REJECTED"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Chỉ có thể gửi duyệt tin đang ở trạng thái Nháp hoặc Bị từ chối (trạng thái hiện tại: {job.status})",
        )

    _validate_job_submission(
        job.title, job.industry_id, job.province_id, job.description,
        job.requirements, job.employment_type, job.experience_level,
        job.deadline, job.salary_min, job.salary_max, job.positions,
    )

    old_status = job.status
    job.status = "PENDING"
    job.reject_reason = None  # Xóa lý do từ chối cũ nếu có

    _audit(db, user, "SUBMIT_JOB", job, {"status": old_status}, {"status": job.status})
    db.commit()
    db.refresh(job)
    return to_job_response(db, job)


def close_job(db: Session, user: User, job_id: int) -> JobResponse:
    """Đóng tin tuyển dụng đang mở (APPROVED -> CLOSED) (FR-M2-04, BR-04)."""
    company, _ = require_approved_company(db, user)
    job = get_employer_job_or_404(db, job_id, company.id)

    if job.status != "APPROVED":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Chỉ có thể đóng tin tuyển dụng đang hiển thị tuyển dụng (APPROVED) (trạng thái hiện tại: {job.status})",
        )

    old_status = job.status
    job.status = "CLOSED"
    job.closed_at = _utcnow()

    _audit(db, user, "CLOSE_JOB", job, {"status": old_status}, {"status": job.status, "closed_at": str(job.closed_at)})
    db.commit()
    db.refresh(job)
    return to_job_response(db, job)


def reopen_job(db: Session, user: User, job_id: int, new_deadline: date | None = None) -> JobResponse:
    """Mở lại tin tuyển dụng đã đóng (CLOSED -> PENDING theo bảng 3.7.1) (FR-M2-04)."""
    company, _ = require_approved_company(db, user)
    job = get_employer_job_or_404(db, job_id, company.id)

    if job.status != "CLOSED":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Chỉ có thể mở lại tin đang ở trạng thái Đã đóng (CLOSED) (trạng thái hiện tại: {job.status})",
        )

    target_deadline = new_deadline or job.deadline
    if not target_deadline or target_deadline < date.today():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Hạn nộp của tin đã quá hạn. Vui lòng cung cấp hạn nộp mới (hôm nay hoặc tương lai) để mở lại tin.",
        )

    old_status = job.status
    job.deadline = target_deadline
    job.status = "PENDING"
    job.closed_at = None

    _audit(db, user, "REOPEN_JOB", job, {"status": old_status}, {"status": job.status, "deadline": str(job.deadline)})
    db.commit()
    db.refresh(job)
    return to_job_response(db, job)


def extend_job(db: Session, user: User, job_id: int, data: JobExtendRequest) -> JobResponse:
    """Gia hạn tin tuyển dụng sắp hết hạn hoặc đã hết hạn (FR-M2-05, SRS 3.7.1)."""
    company, _ = require_approved_company(db, user)
    job = get_employer_job_or_404(db, job_id, company.id)

    if job.status not in ("APPROVED", "EXPIRED"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Chỉ có thể gia hạn tin đang mở hoặc đã hết hạn (trạng thái hiện tại: {job.status})",
        )

    old_status = job.status
    old_deadline = str(job.deadline) if job.deadline else None

    job.deadline = data.deadline
    # Bảng 3.7.1: Hết hạn -> Chờ duyệt khi gia hạn
    if job.status == "EXPIRED":
        job.status = "PENDING"

    _audit(
        db, user, "EXTEND_JOB", job,
        {"status": old_status, "deadline": old_deadline},
        {"status": job.status, "deadline": str(job.deadline)},
    )
    db.commit()
    db.refresh(job)
    return to_job_response(db, job)


def delete_draft_job(db: Session, user: User, job_id: int) -> dict:
    """Xóa tin nháp hoặc tin bị từ chối."""
    company, _ = require_approved_company(db, user)
    job = get_employer_job_or_404(db, job_id, company.id)

    if job.status not in ("DRAFT", "REJECTED"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Chỉ có thể xóa tin đang ở trạng thái Nháp hoặc Bị từ chối (trạng thái hiện tại: {job.status})",
        )

    db.query(JobSkill).filter(JobSkill.job_id == job.id).delete()
    db.delete(job)
    _audit(db, user, "DELETE_JOB", job, {"id": job.id, "title": job.title, "status": job.status}, {})
    db.commit()
    return {"message": "Đã xóa tin tuyển dụng thành công"}


# ---------- Admin: Kiểm duyệt tin tuyển dụng (FR-M2-06, FR-M2-07, PB-017) ----------

def admin_list_jobs(
    db: Session,
    status_filter: str | None = None,
    company_id: int | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> JobListResponse:
    query = db.query(Job)
    if status_filter:
        query = query.filter(Job.status == status_filter)
    if company_id:
        query = query.filter(Job.company_id == company_id)
    if q and q.strip():
        query = query.filter(Job.title.ilike(f"%{q.strip()}%"))

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    items = (
        query.order_by(Job.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return JobListResponse(
        items=[to_job_response(db, j) for j in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def admin_get_job(db: Session, job_id: int) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tin tuyển dụng")
    return to_job_response(db, job)


def approve_job(db: Session, admin: User, job_id: int) -> JobResponse:
    """Admin duyệt tin tuyển dụng (FR-M2-06, Bảng 3.7.1)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tin tuyển dụng")

    if job.status != "PENDING":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Chỉ có thể duyệt tin đang ở trạng thái Chờ duyệt (PENDING) (trạng thái hiện tại: {job.status})",
        )

    old_status = job.status
    now = _utcnow()
    job.status = "APPROVED"
    job.reviewed_by = admin.id
    job.reviewed_at = now
    job.published_at = now
    job.reject_reason = None

    # Thông báo cho người tạo tin
    _notify_employer(
        db, job.created_by, job, "JOB_APPROVED",
        "Tin tuyển dụng đã được duyệt",
        f"Tin tuyển dụng '{job.title}' của bạn đã được duyệt thành công và hiển thị công khai.",
    )
    _audit(db, admin, "APPROVE_JOB", job, {"status": old_status}, {"status": job.status, "reviewed_by": admin.id})
    db.commit()
    db.refresh(job)
    return to_job_response(db, job)


def reject_job(db: Session, admin: User, job_id: int, reason: str) -> JobResponse:
    """Admin từ chối tin tuyển dụng kèm lý do (FR-M2-06, BR-14)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tin tuyển dụng")

    if job.status != "PENDING":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Chỉ có thể từ chối tin đang ở trạng thái Chờ duyệt (PENDING) (trạng thái hiện tại: {job.status})",
        )

    old_status = job.status
    job.status = "REJECTED"
    job.reject_reason = reason
    job.reviewed_by = admin.id
    job.reviewed_at = _utcnow()

    # Thông báo cho người tạo tin
    _notify_employer(
        db, job.created_by, job, "JOB_REJECTED",
        "Tin tuyển dụng bị từ chối",
        f"Tin tuyển dụng '{job.title}' của bạn đã bị từ chối với lý do: {reason}",
    )
    _audit(
        db, admin, "REJECT_JOB", job,
        {"status": old_status},
        {"status": job.status, "reject_reason": reason, "reviewed_by": admin.id},
    )
    db.commit()
    db.refresh(job)
    return to_job_response(db, job)


def remove_job(db: Session, admin: User, job_id: int, reason: str) -> JobResponse:
    """Admin gỡ tin tuyển dụng vi phạm (FR-M2-07)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tin tuyển dụng")

    old_status = job.status
    now = _utcnow()
    job.status = "CLOSED"
    job.removed_by = admin.id
    job.removed_at = now
    job.removal_reason = reason
    job.closed_at = now

    _notify_employer(
        db, job.created_by, job, "JOB_REMOVED",
        "Tin tuyển dụng bị gỡ vi phạm",
        f"Tin tuyển dụng '{job.title}' của bạn đã bị gỡ do vi phạm với lý do: {reason}",
    )
    _audit(
        db, admin, "REMOVE_JOB", job,
        {"status": old_status},
        {"status": job.status, "removal_reason": reason, "removed_by": admin.id},
    )
    db.commit()
    db.refresh(job)
    return to_job_response(db, job)
