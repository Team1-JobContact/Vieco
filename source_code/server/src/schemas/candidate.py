import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

Gender = Literal["MALE", "FEMALE", "OTHER"]
Visibility = Literal["PUBLIC", "PRIVATE"]


class _ProfileFields(BaseModel):
    """Các trường chung khi tạo/cập nhật hồ sơ (FR-M1-09, FR-M1-12)."""

    full_name: str | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    gender: Gender | None = None
    address: str | None = None
    province_id: int | None = None
    headline: str | None = None
    summary: str | None = None
    visibility: Visibility | None = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not 2 <= len(v) <= 150:
            raise ValueError("Họ tên phải từ 2 đến 150 ký tự")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if not re.fullmatch(r"\+?\d{9,15}", v):
            raise ValueError("Số điện thoại không hợp lệ")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date | None) -> date | None:
        if v is not None and (v >= date.today() or v.year < 1900):
            raise ValueError("Ngày sinh không hợp lệ")
        return v

    @field_validator("address", "headline", "summary")
    @classmethod
    def strip_text(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 255:
            raise ValueError("Địa chỉ tối đa 255 ký tự")
        return v

    @field_validator("headline")
    @classmethod
    def validate_headline(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 150:
            raise ValueError("Chức danh tối đa 150 ký tự")
        return v

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 5000:
            raise ValueError("Giới thiệu bản thân tối đa 5000 ký tự")
        return v


class ProfileCreate(_ProfileFields):
    pass


class ProfileUpdate(_ProfileFields):
    """PATCH: chỉ cập nhật các trường được gửi lên; gửi null để xóa giá trị trường tùy chọn."""

    @field_validator("full_name", "visibility", mode="before")
    @classmethod
    def not_null(cls, v):
        if v is None:
            raise ValueError("Trường này không được để trống")
        return v


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    email: str
    full_name: str
    phone: str | None = None
    avatar_url: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    address: str | None = None
    province_id: int | None = None
    headline: str | None = None
    summary: str | None = None
    visibility: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CVResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_size: int
    is_default: bool
    created_at: datetime | None = None


class CVListResponse(BaseModel):
    items: list[CVResponse]
    total: int
    max_count: int
    max_size_mb: int
    allowed_extensions: list[str]
