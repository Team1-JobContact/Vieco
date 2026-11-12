import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

CompanySize = Literal["1-50", "51-200", "201-500", "501-1000", "1000+"]
CompanyStatus = Literal["PENDING", "APPROVED", "REJECTED"]

URL_RE = re.compile(r"https?://[^\s/$.?#][^\s]*", re.IGNORECASE)


def _strip_or_none(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return v or None


class _CompanyFields(BaseModel):
    """Thông tin hồ sơ công ty (FR-M1-13)."""

    name: str | None = None
    description: str | None = None
    industry_id: int | None = None
    size: CompanySize | None = None
    website: str | None = None
    address: str | None = None
    province_id: int | None = None

    @field_validator("name", "description", "website", "address", mode="before")
    @classmethod
    def strip_text(cls, v):
        return _strip_or_none(v) if isinstance(v, str) else v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None and not 2 <= len(v) <= 200:
            raise ValueError("Tên công ty phải từ 2 đến 200 ký tự")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 10000:
            raise ValueError("Giới thiệu công ty tối đa 10000 ký tự")
        return v

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if len(v) > 255 or not URL_RE.fullmatch(v):
            raise ValueError("Website phải là URL hợp lệ bắt đầu bằng http:// hoặc https://")
        return v

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 255:
            raise ValueError("Địa chỉ tối đa 255 ký tự")
        return v


class CompanyCreate(_CompanyFields):
    # Thông tin bắt buộc để gửi duyệt (UC-08: thiếu thông tin bắt buộc thì không cho gửi duyệt)
    name: str
    industry_id: int
    size: CompanySize
    address: str
    province_id: int


class CompanyUpdate(_CompanyFields):
    """PATCH: chỉ cập nhật trường được gửi; trường bắt buộc không được gửi null."""

    @field_validator("name", "industry_id", "size", "address", "province_id", mode="before")
    @classmethod
    def not_null(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("Trường này không được để trống")
        return v


class RejectRequest(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        v = v.strip()
        if not 10 <= len(v) <= 500:
            raise ValueError("Lý do từ chối phải từ 10 đến 500 ký tự")
        return v


class CompanyResponse(BaseModel):
    id: int
    name: str
    slug: str
    logo_url: str | None = None
    description: str | None = None
    industry_id: int | None = None
    size: str | None = None
    website: str | None = None
    address: str | None = None
    province_id: int | None = None
    status: str
    reject_reason: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MyCompanyResponse(CompanyResponse):
    member_role: str


class AdminCompanyResponse(CompanyResponse):
    reviewed_by: int | None = None
    owner_id: int | None = None
    owner_email: str | None = None
    owner_name: str | None = None


class AdminCompanyListResponse(BaseModel):
    items: list[AdminCompanyResponse]
    total: int
    page: int
    page_size: int
