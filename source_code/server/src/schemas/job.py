from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

JobStatus = Literal["DRAFT", "PENDING", "APPROVED", "REJECTED", "CLOSED", "EXPIRED"]
EmploymentType = Literal["FULL_TIME", "PART_TIME", "INTERNSHIP", "CONTRACT", "FREELANCE"]
ExperienceLevel = Literal["NONE", "UNDER_1", "FROM_1_TO_3", "FROM_3_TO_5", "OVER_5"]


def _strip_or_none(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return v or None


class SkillItem(BaseModel):
    id: int
    name: str


class JobBase(BaseModel):
    """Các trường thông tin cơ bản của tin tuyển dụng (FR-M2-01)."""

    title: str | None = None
    industry_id: int | None = None
    province_id: int | None = None
    work_address: str | None = None
    description: str | None = None
    requirements: str | None = None
    benefits: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "VND"
    experience_level: ExperienceLevel | None = None
    employment_type: EmploymentType | None = None
    positions: int = 1
    deadline: date | None = None
    skill_ids: list[int] = Field(default_factory=list)

    @field_validator("title", "work_address", "description", "requirements", "benefits", mode="before")
    @classmethod
    def strip_text(cls, v):
        return _strip_or_none(v) if isinstance(v, str) else v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        if v is not None and not 5 <= len(v) <= 200:
            raise ValueError("Tiêu đề tin tuyển dụng phải từ 5 đến 200 ký tự")
        return v

    @field_validator("positions")
    @classmethod
    def validate_positions(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Số lượng tuyển dụng phải lớn hơn hoặc bằng 1")
        return v

    @field_validator("salary_min", "salary_max")
    @classmethod
    def validate_salary(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("Mức lương không được âm")
        return v


class JobCreate(JobBase):
    """Payload tạo tin tuyển dụng hoặc lưu nháp (FR-M2-01, FR-M2-02, UC-04)."""

    title: str
    action: Literal["draft", "submit"] = "draft"

    @field_validator("title")
    @classmethod
    def validate_title_required(cls, v: str) -> str:
        v = (v or "").strip()
        if not 5 <= len(v) <= 200:
            raise ValueError("Tiêu đề tin tuyển dụng phải từ 5 đến 200 ký tự")
        return v


class JobUpdate(JobBase):
    """Payload cập nhật tin tuyển dụng (FR-M2-03)."""

    pass


class JobExtendRequest(BaseModel):
    """Gia hạn tin tuyển dụng (FR-M2-05)."""

    deadline: date

    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Hạn nộp mới phải là ngày hiện tại hoặc tương lai")
        return v


class JobRejectRequest(BaseModel):
    """Admin từ chối tin tuyển dụng (FR-M2-06, BR-14)."""

    reason: str

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        v = (v or "").strip()
        if not 10 <= len(v) <= 500:
            raise ValueError("Lý do từ chối phải từ 10 đến 500 ký tự")
        return v


class JobRemoveRequest(BaseModel):
    """Admin gỡ tin vi phạm (FR-M2-07)."""

    reason: str

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        v = (v or "").strip()
        if not 10 <= len(v) <= 500:
            raise ValueError("Lý do gỡ tin phải từ 10 đến 500 ký tự")
        return v


class JobResponse(BaseModel):
    """Chi tiết tin tuyển dụng trả về cho client."""

    id: int
    company_id: int
    company_name: str | None = None
    created_by: int
    title: str
    industry_id: int | None = None
    industry_name: str | None = None
    province_id: int | None = None
    province_name: str | None = None
    work_address: str | None = None
    description: str | None = None
    requirements: str | None = None
    benefits: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "VND"
    experience_level: str | None = None
    employment_type: str | None = None
    positions: int
    deadline: date | None = None
    status: JobStatus
    reject_reason: str | None = None
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    published_at: datetime | None = None
    closed_at: datetime | None = None
    removed_by: int | None = None
    removed_at: datetime | None = None
    removal_reason: str | None = None
    view_count: int
    created_at: datetime
    updated_at: datetime
    skills: list[SkillItem] = Field(default_factory=list)


class JobListResponse(BaseModel):
    """Danh sách tin tuyển dụng có phân trang."""

    items: list[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

