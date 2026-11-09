"""Module M2: Tin tuyển dụng và ứng tuyển.

LƯU Ý: từ điển dữ liệu của M2 (mục 4.3) chưa có trong tài liệu thiết kế v1.0;
các bảng dưới đây được suy ra từ SRS (FR-M2-*, mục 3.6, 3.7, BR-03..BR-08, BR-13..BR-18).
"""
from sqlalchemy import (
    BigInteger, CheckConstraint, Column, Date, DateTime, Index, Integer, String, Text,
    UniqueConstraint, text,
)
from src.models.base import BaseModel, fk, in_check
from src.models.enums import (
    APPLICATION_STATUSES, EMPLOYMENT_TYPES, EXPERIENCE_LEVELS, JOB_STATUSES,
)


class Job(BaseModel):
    __tablename__ = "jobs"
    __table_args__ = (
        in_check("status", JOB_STATUSES, "status"),
        in_check("employment_type", EMPLOYMENT_TYPES, "employment_type"),
        in_check("experience_level", EXPERIENCE_LEVELS, "experience_level"),
        CheckConstraint("salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
                        name="salary_range"),
        CheckConstraint("positions > 0", name="positions"),
        Index("ix_jobs_status_deadline", "status", "deadline"),
        Index("ix_jobs_company_status", "company_id", "status"),
    )

    company_id = fk("companies.id")                      # BR-13
    created_by = fk("users.id")                          # nhà tuyển dụng tạo tin
    title = Column(String(200), nullable=False)
    industry_id = fk("industries.id", nullable=True)
    province_id = fk("provinces.id", nullable=True)
    work_address = Column(String(255))
    # Các trường dưới đây cho phép NULL để hỗ trợ lưu nháp (FR-M2-02);
    # tầng ứng dụng bắt buộc đủ khi gửi duyệt (SRS mục 3.6).
    description = Column(Text)
    requirements = Column(Text)
    benefits = Column(Text)
    salary_min = Column(BigInteger)
    salary_max = Column(BigInteger)
    salary_currency = Column(String(3), nullable=False, default="VND", server_default="VND")
    experience_level = Column(String(30))
    employment_type = Column(String(20))
    positions = Column(Integer, nullable=False, default=1, server_default=text("1"))
    deadline = Column(Date)                              # hạn nộp
    status = Column(String(20), nullable=False, default="DRAFT", server_default="DRAFT")
    reject_reason = Column(String(500))                  # BR-14
    reviewed_by = fk("users.id", nullable=True)
    reviewed_at = Column(DateTime)
    published_at = Column(DateTime)
    closed_at = Column(DateTime)
    # Admin gỡ tin vi phạm (FR-M2-07) mà không làm thay đổi vòng đời 6 trạng thái của BR-04.
    removed_by = fk("users.id", nullable=True)
    removed_at = Column(DateTime)
    removal_reason = Column(String(500))
    view_count = Column(Integer, nullable=False, default=0, server_default=text("0"))


class JobSkill(BaseModel):
    __tablename__ = "job_skills"
    __table_args__ = (UniqueConstraint("job_id", "skill_id", name="uq_job_skills_job_skill"),)

    job_id = fk("jobs.id", ondelete="CASCADE")
    skill_id = fk("skills.id")


class Application(BaseModel):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("job_id", "candidate_profile_id", name="uq_applications_job_candidate"),  # BR-05
        in_check("status", APPLICATION_STATUSES, "status"),
        Index("ix_applications_job_status", "job_id", "status"),
    )

    job_id = fk("jobs.id")
    candidate_profile_id = fk("candidate_profiles.id")
    cv_id = fk("cvs.id")                                 # BR-15: CV chọn tại thời điểm nộp
    cover_letter = Column(Text)
    status = Column(String(20), nullable=False, default="NEW", server_default="NEW")
    withdrawn_at = Column(DateTime)                      # UC-07


class ApplicationStatusHistory(BaseModel):
    __tablename__ = "application_status_history"
    __table_args__ = (
        in_check("from_status", APPLICATION_STATUSES, "from_status"),
        in_check("to_status", APPLICATION_STATUSES, "to_status"),
        Index("ix_application_status_history_application_created", "application_id", "created_at"),
    )

    application_id = fk("applications.id")
    from_status = Column(String(20))                     # NULL khi tạo đơn
    to_status = Column(String(20), nullable=False)
    changed_by = fk("users.id")                          # BR-07
    note = Column(String(500))


class SavedJob(BaseModel):
    __tablename__ = "saved_jobs"
    __table_args__ = (UniqueConstraint("candidate_profile_id", "job_id", name="uq_saved_jobs_candidate_job"),)

    candidate_profile_id = fk("candidate_profiles.id", ondelete="CASCADE")
    job_id = fk("jobs.id", ondelete="CASCADE")
