"""Module M1: Công ty và thành viên công ty."""
from sqlalchemy import Column, DateTime, String, Text
from src.models.base import BaseModel, fk, in_check
from src.models.enums import COMPANY_STATUSES, MEMBER_ROLES


class Company(BaseModel):
    __tablename__ = "companies"
    __table_args__ = (in_check("status", COMPANY_STATUSES, "status"),)

    name = Column(String(200), nullable=False)
    slug = Column(String(220), nullable=False, unique=True)
    logo_url = Column(String(500))
    description = Column(Text)
    industry_id = fk("industries.id", nullable=True)
    size = Column(String(30))  # ví dụ 1-50, 51-200
    website = Column(String(255))
    address = Column(String(255))
    province_id = fk("provinces.id", nullable=True)
    status = Column(String(20), nullable=False, default="PENDING", server_default="PENDING", index=True)
    reject_reason = Column(String(500))
    reviewed_by = fk("users.id", nullable=True)
    reviewed_at = Column(DateTime)


class CompanyMember(BaseModel):
    __tablename__ = "company_members"
    __table_args__ = (in_check("member_role", MEMBER_ROLES, "member_role"),)

    company_id = fk("companies.id")
    user_id = fk("users.id", unique=True)  # mỗi nhà tuyển dụng thuộc một công ty
    member_role = Column(String(20), nullable=False, default="MEMBER", server_default="MEMBER")
