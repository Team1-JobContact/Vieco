"""Module M1: Hồ sơ ứng viên, học vấn, kinh nghiệm, kỹ năng, CV."""
from sqlalchemy import Column, Date, DateTime, Integer, String, Text, UniqueConstraint
from src.models.base import BaseModel, fk, flag, in_check
from src.models.enums import GENDERS, SKILL_LEVELS, VISIBILITIES


class CandidateProfile(BaseModel):
    __tablename__ = "candidate_profiles"
    __table_args__ = (
        in_check("gender", GENDERS, "gender"),
        in_check("visibility", VISIBILITIES, "visibility"),
    )

    user_id = fk("users.id", ondelete="CASCADE", unique=True)
    date_of_birth = Column(Date)
    gender = Column(String(10))
    address = Column(String(255))
    province_id = fk("provinces.id", nullable=True)
    headline = Column(String(150))
    summary = Column(Text)
    visibility = Column(String(10), nullable=False, default="PUBLIC", server_default="PUBLIC")


class Education(BaseModel):
    __tablename__ = "educations"

    candidate_profile_id = fk("candidate_profiles.id", ondelete="CASCADE")
    school_name = Column(String(200), nullable=False)
    major = Column(String(150))
    degree = Column(String(50))
    start_date = Column(Date)
    end_date = Column(Date)
    description = Column(Text)


class WorkExperience(BaseModel):
    __tablename__ = "work_experiences"

    candidate_profile_id = fk("candidate_profiles.id", ondelete="CASCADE")
    company_name = Column(String(200), nullable=False)
    position = Column(String(150), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)  # NULL nếu đang làm
    description = Column(Text)


class CandidateSkill(BaseModel):
    __tablename__ = "candidate_skills"
    __table_args__ = (
        UniqueConstraint("candidate_profile_id", "skill_id", name="uq_candidate_skills_profile_skill"),
        in_check("level", SKILL_LEVELS, "level"),
    )

    candidate_profile_id = fk("candidate_profiles.id", ondelete="CASCADE")
    skill_id = fk("skills.id")
    level = Column(String(20))


class CV(BaseModel):
    __tablename__ = "cvs"

    candidate_profile_id = fk("candidate_profiles.id")
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # byte
    is_default = flag(False)
    # Bổ sung so với ERD: CV đã gắn với đơn ứng tuyển thì không xóa cứng (BR-15), dùng xóa mềm.
    deleted_at = Column(DateTime)
    # Giới hạn tối đa 5 CV/hồ sơ do tầng ứng dụng kiểm soát.
