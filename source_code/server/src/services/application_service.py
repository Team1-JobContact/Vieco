from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from src.models.profile import CV, CandidateProfile
from src.models.recruitment import Application, ApplicationStatusHistory, Job
from src.models.engagement import Notification
from src.models.company import CompanyMember
from src.services import candidate_service, company_service
from src.services.auth_service import _utcnow
from src.services.public_service import public_jobs_query

TRANSITIONS = {"NEW": {"VIEWED","INTERVIEW","REJECTED"}, "VIEWED": {"INTERVIEW","REJECTED"},
               "INTERVIEW": {"ACCEPTED","REJECTED"}}

def fields(row):
    return {key: getattr(row,key) for key in ("id","job_id","candidate_profile_id","cv_id","cover_letter","status","withdrawn_at","created_at","updated_at")}

def history(db,row,user,old,note=None):
    db.add(ApplicationStatusHistory(application_id=row.id, from_status=old,to_status=row.status,changed_by=user.id,note=note))

def create_application(db,user,data):
    profile = candidate_service.get_profile_or_404(db,user)
    job = public_jobs_query(db).filter(Job.id == data.job_id).with_for_update().first()
    if job is None:
        raise HTTPException(409,"Tin không còn nhận ứng tuyển")
    cv = db.query(CV).filter(CV.id == data.cv_id,CV.candidate_profile_id == profile.id,CV.deleted_at.is_(None)).first()
    if cv is None:
        raise HTTPException(404,"Không tìm thấy CV của bạn")
    row = Application(job_id=job.id,candidate_profile_id=profile.id,cv_id=cv.id,cover_letter=data.cover_letter,status="NEW")
    db.add(row)
    try:
        db.flush()
        history(db,row,user,None)
        for (uid,) in db.query(CompanyMember.user_id).filter(CompanyMember.company_id == job.company_id):
            db.add(Notification(user_id=uid,type="APPLICATION_NEW",title="Đơn ứng tuyển mới",message=f"Tin {job.title} có đơn ứng tuyển mới",reference_type="APPLICATION",reference_id=row.id))
        db.commit()
        from src.services.notification_service import send_for_reference
        send_for_reference(db,"APPLICATION",row.id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,"Bạn đã ứng tuyển tin này")
    return fields(row)

def paginate(query,page,page_size):
    total=query.count()
    rows=query.order_by(Application.created_at.desc(),Application.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    return dict(items=[fields(r) for r in rows],total=total,page=page,page_size=page_size)

def my_applications(db,user,page,page_size):
    profile=candidate_service.find_profile(db,user)
    if profile is None:
        return dict(items=[],total=0,page=page,page_size=page_size)
    return paginate(db.query(Application).filter(Application.candidate_profile_id == profile.id),page,page_size)

def employer_applications(db,user,job_id,page,page_size):
    company,_=company_service.get_membership_or_404(db,user)
    if not db.query(Job.id).filter(Job.id == job_id,Job.company_id == company.id).first():
        raise HTTPException(404,"Không tìm thấy tin của công ty bạn")
    return paginate(db.query(Application).filter(Application.job_id == job_id),page,page_size)

def withdraw(db,user,application_id):
    profile=candidate_service.get_profile_or_404(db,user)
    row=db.query(Application).filter(Application.id == application_id,Application.candidate_profile_id == profile.id).with_for_update().first()
    if row is None:
        raise HTTPException(404,"Không tìm thấy đơn ứng tuyển")
    if row.status not in ("NEW","VIEWED"):
        raise HTTPException(409,"Chỉ rút đơn khi chưa phỏng vấn hoặc có kết quả")
    old=row.status
    row.status="WITHDRAWN"
    row.withdrawn_at=_utcnow()
    history(db,row,user,old)
    db.commit()
    return fields(row)

def update_status(db,user,application_id,data):
    company,_=company_service.get_membership_or_404(db,user)
    row=db.query(Application).join(Job,Job.id == Application.job_id).filter(Application.id == application_id,Job.company_id == company.id).with_for_update().first()
    if row is None:
        raise HTTPException(404,"Không tìm thấy đơn của công ty bạn")
    if data.status not in TRANSITIONS.get(row.status,set()):
        raise HTTPException(409,"Chuyển trạng thái đơn không hợp lệ")
    old=row.status
    row.status=data.status
    history(db,row,user,old,data.note)
    profile=db.get(CandidateProfile,row.candidate_profile_id)
    db.add(Notification(user_id=profile.user_id,type="APPLICATION_STATUS",title="Cập nhật đơn ứng tuyển",message=f"Đơn ứng tuyển chuyển sang {data.status}",reference_type="APPLICATION",reference_id=row.id))
    db.commit()
    from src.services.notification_service import send_for_reference
    send_for_reference(db,"APPLICATION",row.id)
    return fields(row)
