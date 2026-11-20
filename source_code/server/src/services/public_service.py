from fastapi import HTTPException
from sqlalchemy import func, or_
from src.models.company import Company
from src.models.recruitment import Job
from src.services import job_service, candidate_service, auth_service
from src.schemas.candidate import ProfileCreate
from src.utils.dates import business_today as today

def public_jobs_query(db):
    return db.query(Job).join(Company, Company.id == Job.company_id).filter(
        Job.status == "APPROVED", Company.status == "APPROVED",
        Job.removed_at.is_(None), Job.deadline >= today())

def list_jobs(db, q, industry_id, province_id, skill_id, employment_type, experience_level, salary_min, salary_max,
              page, page_size, company_id=None, sort="newest"):
    from src.models.catalog import Skill
    from src.models.recruitment import JobSkill
    query = public_jobs_query(db)
    if q and q.strip():
        like = f"%{q.strip()}%"
        skill_jobs = db.query(JobSkill.job_id).join(Skill, Skill.id == JobSkill.skill_id).filter(Skill.name.ilike(like))
        query = query.filter(or_(Job.title.ilike(like), Company.name.ilike(like), Job.id.in_(skill_jobs)))
    for field, value in ((Job.industry_id, industry_id), (Job.province_id, province_id), (Job.company_id, company_id),
                         (Job.employment_type, employment_type), (Job.experience_level, experience_level)):
        if value is not None:
            query = query.filter(field == value)
    if skill_id is not None:
        query = query.filter(Job.id.in_(db.query(JobSkill.job_id).filter(JobSkill.skill_id == skill_id)))
    if salary_min is not None:
        query = query.filter(Job.salary_max >= salary_min)
    if salary_max is not None:
        query = query.filter(Job.salary_min <= salary_max)
    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        raise HTTPException(422, "Khoảng lương không hợp lệ")
    total = query.count()
    order = {"salary": (Job.salary_max.desc(), Job.id.desc()), "deadline": (Job.deadline.asc(), Job.id.desc())}.get(
        sort, (Job.published_at.desc(), Job.id.desc()))
    rows = query.order_by(*order).offset((page-1)*page_size).limit(page_size).all()
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

COMPANY_KEYS = ("id","name","slug","logo_url","cover_url","description","industry_id","size","website","address","province_id")

def company_fields(db, row, open_jobs=None):
    from src.models.catalog import Industry, Province
    data = {key: getattr(row,key) for key in COMPANY_KEYS}
    industry = db.get(Industry, row.industry_id) if row.industry_id else None
    province = db.get(Province, row.province_id) if row.province_id else None
    data["industry_name"] = industry.name if industry else None
    data["province_name"] = province.name if province else None
    data["open_jobs"] = open_jobs if open_jobs is not None else public_jobs_query(db).filter(Job.company_id == row.id).count()
    return data

def list_companies(db, q, industry_id, province_id, page, page_size):
    """Danh sách công ty đã duyệt (FR-M1-14), kèm số vị trí đang tuyển; công ty nhiều tin đứng trước."""
    open_jobs = (public_jobs_query(db).with_entities(Job.company_id.label("company_id"), func.count(Job.id).label("n"))
                 .group_by(Job.company_id).subquery())
    query = db.query(Company, func.coalesce(open_jobs.c.n, 0)).outerjoin(
        open_jobs, open_jobs.c.company_id == Company.id).filter(Company.status == "APPROVED")
    if q and q.strip():
        query = query.filter(Company.name.ilike(f"%{q.strip()}%"))
    if industry_id is not None:
        query = query.filter(Company.industry_id == industry_id)
    if province_id is not None:
        query = query.filter(Company.province_id == province_id)
    total = query.count()
    rows = query.order_by(func.coalesce(open_jobs.c.n, 0).desc(), Company.name, Company.id).offset(
        (page-1)*page_size).limit(page_size).all()
    return dict(items=[company_fields(db, c, n) for c, n in rows], total=total, page=page, page_size=page_size,
                total_pages=(total+page_size-1)//page_size)

def get_company(db, company_id):
    row = db.query(Company).filter(Company.id == company_id, Company.status == "APPROVED").first()
    if not row:
        raise HTTPException(404, "Không tìm thấy công ty")
    data = company_fields(db, row)
    from src.services import company_media_service
    data["images"] = company_media_service.list_images(db, row)
    return data

# ---------- Việc đã lưu ----------

def _profile_for_saving(db, user):
    return candidate_service.get_or_create_profile(db, user)

def list_saved_jobs(db, user):
    from src.models.recruitment import SavedJob
    profile = candidate_service.find_profile(db, user)
    if profile is None:
        return dict(items=[], total=0)
    rows = (public_jobs_query(db).join(SavedJob, SavedJob.job_id == Job.id)
            .filter(SavedJob.candidate_profile_id == profile.id).order_by(SavedJob.created_at.desc(), SavedJob.id.desc()).all())
    return dict(items=[job_service.to_job_response(db,j) for j in rows], total=len(rows))

def save_job(db, user, job_id):
    from sqlalchemy.exc import IntegrityError
    from src.models.recruitment import SavedJob
    if public_jobs_query(db).filter(Job.id == job_id).first() is None:
        raise HTTPException(404, "Không tìm thấy tin tuyển dụng")
    profile = _profile_for_saving(db, user)
    if not db.query(SavedJob.id).filter(SavedJob.candidate_profile_id == profile.id, SavedJob.job_id == job_id).first():
        db.add(SavedJob(candidate_profile_id=profile.id, job_id=job_id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    return {"job_id": job_id, "saved": True}

def unsave_job(db, user, job_id):
    from src.models.recruitment import SavedJob
    profile = candidate_service.find_profile(db, user)
    if profile is not None:
        db.query(SavedJob).filter(SavedJob.candidate_profile_id == profile.id, SavedJob.job_id == job_id).delete()
        db.commit()
    return {"job_id": job_id, "saved": False}

def get_profile(db, user):
    account = auth_service.to_user_response(user,user.role_name).model_dump()
    profile = candidate_service.find_profile(db,user) if user.role_name == "CANDIDATE" else None
    account["profile"] = candidate_service.to_profile_response(profile,user) if profile else None
    return account

def update_profile(db, user, data):
    if candidate_service.find_profile(db,user):
        return candidate_service.update_profile(db,user,data)
    return candidate_service.create_profile(db,user,ProfileCreate(**data.model_dump(exclude_unset=True)))
