from fastapi import Depends, Query
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.middlewares.auth import get_current_user, require_roles
from src.models.user import User
from src.schemas.design import (ApprovalRequest, CategoryCreate, EmailRequest, TokenRequest,
    ResetPasswordRequest, ApplicationCreate, ApplicationStatusUpdate)
from src.schemas.candidate import ProfileUpdate
from src.schemas.company import CompanyCreate
from src.schemas.job import JobCreate, JobUpdate, EmploymentType, ExperienceLevel
from src.services import (public_service, catalog_service, company_service, job_service,
    application_service, notification_service, email_service)

candidate = require_roles("CANDIDATE")
employer = require_roles("EMPLOYER")
admin = require_roles("ADMIN")

def verify_email(data: TokenRequest, db: Session = Depends(get_db)):
    return email_service.verify_email(db,data.token)

def forgot_password(data: EmailRequest, db: Session = Depends(get_db)):
    return email_service.forgot_password(db,data.email)

def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    return email_service.reset_password(db,data)

def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return public_service.get_profile(db,user)

def update_profile(data: ProfileUpdate, user: User = Depends(candidate), db: Session = Depends(get_db)):
    return public_service.update_profile(db,user,data)

def create_category(data: CategoryCreate, _: User = Depends(admin), db: Session = Depends(get_db)):
    return catalog_service.create_category(db,data)

def create_company(data: CompanyCreate, user: User = Depends(employer), db: Session = Depends(get_db)):
    return company_service.create_company(db,user,data)

def get_company(company_id: int, db: Session = Depends(get_db)):
    return public_service.get_company(db,company_id)

def approve_company(company_id: int, data: ApprovalRequest, user: User = Depends(admin), db: Session = Depends(get_db)):
    if data.status == "APPROVED":
        return company_service.approve_company(db,user,company_id)
    return company_service.reject_company(db,user,company_id,data.reason)

def list_jobs(q: str | None = Query(None,max_length=100), industry_id: int | None = Query(None,gt=0),
              province_id: int | None = Query(None,gt=0), skill_id: int | None = Query(None,gt=0),
              employment_type: EmploymentType | None = None, experience_level: ExperienceLevel | None = None,
              salary_min: int | None = Query(None,ge=0), salary_max: int | None = Query(None,ge=0),
              page: int = Query(1,ge=1), page_size: int = Query(20,ge=1,le=100), db: Session = Depends(get_db)):
    return public_service.list_jobs(db,q,industry_id,province_id,skill_id,employment_type,experience_level,salary_min,salary_max,page,page_size)

def get_job(job_id: int, db: Session = Depends(get_db)):
    return public_service.get_job(db,job_id)

def create_job(data: JobCreate, user: User = Depends(employer), db: Session = Depends(get_db)):
    return job_service.create_job(db,user,data)

def update_job(job_id: int, data: JobUpdate, user: User = Depends(employer), db: Session = Depends(get_db)):
    return job_service.update_job(db,user,job_id,data)

def approve_job(job_id: int, data: ApprovalRequest, user: User = Depends(admin), db: Session = Depends(get_db)):
    if data.status == "APPROVED":
        return job_service.approve_job(db,user,job_id)
    return job_service.reject_job(db,user,job_id,data.reason)

def create_application(data: ApplicationCreate, user: User = Depends(candidate), db: Session = Depends(get_db)):
    return application_service.create_application(db,user,data)

def my_applications(page: int = Query(1,ge=1), page_size: int = Query(20,ge=1,le=100),
                    user: User = Depends(candidate), db: Session = Depends(get_db)):
    return application_service.my_applications(db,user,page,page_size)

def withdraw_application(application_id: int, user: User = Depends(candidate), db: Session = Depends(get_db)):
    return application_service.withdraw(db,user,application_id)

def employer_applications(job_id: int, page: int = Query(1,ge=1), page_size: int = Query(20,ge=1,le=100),
                          user: User = Depends(employer), db: Session = Depends(get_db)):
    return application_service.employer_applications(db,user,job_id,page,page_size)

def update_application_status(application_id: int, data: ApplicationStatusUpdate,
                              user: User = Depends(employer), db: Session = Depends(get_db)):
    return application_service.update_status(db,user,application_id,data)

def list_notifications(page: int = Query(1,ge=1), page_size: int = Query(20,ge=1,le=100),
                       user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return notification_service.list_notifications(db,user,page,page_size)

def read_notification(notification_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return notification_service.mark_read(db,user,notification_id)
