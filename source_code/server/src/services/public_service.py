from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from src.models.company import Company
from src.models.recruitment import Job
from src.services import job_service, candidate_service, auth_service
from src.schemas.candidate import ProfileCreate

def today():
    return datetime.now(timezone(timedelta(hours=7))).date()

def public_jobs_query(db):
    return db.query(Job).join(Company, Company.id == Job.company_id).filter(
        Job.status == "APPROVED", Company.status == "APPROVED",
        Job.removed_at.is_(None), Job.deadline >= today())

def list_jobs(db, q, industry_id, province_id, skill_id, employment_type, experience_level, salary_min, salary_max, page, page_size):
    query = public_jobs_query(db)
    if q and q.strip():
        query = query.filter(Job.title.ilike(f"%{q.strip()}%"))
    for field, value in ((Job.industry_id, industry_id), (Job.province_id, province_id),
                         (Job.employment_type, employment_type), (Job.experience_level, experience_level)):
        if value is not None:
            query = query.filter(field == value)
    if skill_id is not None:
        from src.models.recruitment import JobSkill
        query = query.filter(Job.id.in_(db.query(JobSkill.job_id).filter(JobSkill.skill_id == skill_id)))
    if salary_min is not None:
        query = query.filter(Job.salary_max >= salary_min)
    if salary_max is not None:
        query = query.filter(Job.salary_min <= salary_max)
    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        raise HTTPException(422, "Khoảng lương không hợp lệ")
    total = query.count()
    rows = query.order_by(Job.published_at.desc(), Job.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    return dict(items=[job_service.to_job_response(db,j) for j in rows], total=total,
                page=page, page_size=page_size, total_pages=(total+page_size-1)//page_size)

def get_job(db, job_id):
    job = public_jobs_query(db).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Không tìm thấy tin tuyển dụng")
    db.query(Job).filter(Job.id == job.id).update({Job.view_count: Job.view_count+1}, synchronize_session=False)
    db.commit()
    db.refresh(job)
    return job_service.to_job_response(db,job)

def get_company(db, company_id):
    row = db.query(Company).filter(Company.id == company_id, Company.status == "APPROVED").first()
    if not row:
        raise HTTPException(404, "Không tìm thấy công ty")
    return {key: getattr(row,key) for key in ("id","name","slug","logo_url","description","industry_id","size","website","address","province_id")}

def get_profile(db, user):
    account = auth_service.to_user_response(user,user.role_name).model_dump()
    profile = candidate_service.find_profile(db,user) if user.role_name == "CANDIDATE" else None
    account["profile"] = candidate_service.to_profile_response(profile,user) if profile else None
    return account

def update_profile(db, user, data):
    if candidate_service.find_profile(db,user):
        return candidate_service.update_profile(db,user,data)
    return candidate_service.create_profile(db,user,ProfileCreate(**data.model_dump(exclude_unset=True)))
