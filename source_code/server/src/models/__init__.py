"""Import toàn bộ model để Base.metadata (Alembic) nhìn thấy đủ 27 bảng."""
from src.models.catalog import Industry, Province, Skill, StaticPage, SystemSetting
from src.models.user import EmailVerification, PasswordReset, Role, User
from src.models.profile import CV, CandidateProfile, CandidateSkill, Education, WorkExperience
from src.models.company import Company, CompanyMember
from src.models.recruitment import Application, ApplicationStatusHistory, Job, JobSkill, SavedJob
from src.models.engagement import (
    AuditLog, CompanyReview, Conversation, Message, Notification, Report,
)

__all__ = [
    "Industry", "Skill", "Province", "SystemSetting", "StaticPage",
    "Role", "User", "EmailVerification", "PasswordReset",
    "CandidateProfile", "Education", "WorkExperience", "CandidateSkill", "CV",
    "Company", "CompanyMember",
    "Job", "JobSkill", "Application", "ApplicationStatusHistory", "SavedJob",
    "Notification", "Conversation", "Message", "CompanyReview", "Report", "AuditLog",
]
