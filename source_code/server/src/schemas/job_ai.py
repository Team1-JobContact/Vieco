"""AI cho việc làm: chấm điểm CV phù hợp với tin, tối ưu CV theo tin và viết tin tuyển dụng."""
from pydantic import BaseModel, Field, field_validator

from src.schemas.cv_builder import CVContent
from src.schemas.job import EmploymentType, ExperienceLevel

MATCH_LIST_LIMIT = 8      # số ý tối đa mỗi danh sách trong kết quả chấm điểm
MATCH_ITEM_LIMIT = 300    # số ký tự tối đa mỗi ý
CHANGES_LIMIT = 8         # số ghi chú thay đổi tối đa khi tối ưu CV
DRAFT_NOTES_LIMIT = 3000
DRAFT_TEXT_LIMIT = 10000  # bằng giới hạn mô tả/yêu cầu/quyền lợi của tin tuyển dụng

_ID = Field(gt=0, le=2**63 - 1)


class JobCVRequest(BaseModel):
    job_id: int = _ID
    cv_id: int = _ID


class JobMatchResponse(BaseModel):
    job_id: int
    cv_id: int
    cv_name: str
    score: int                 # 0-100
    verdict: str               # nhận xét ngắn
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    gaps: list[str]
    tips: list[str]


class CVTailorResponse(BaseModel):
    job_id: int
    job_title: str
    company_name: str | None = None
    source_cv_id: int
    data: CVContent
    template: str = "elegant"
    photo: str | None = None   # ảnh của CV gốc (CV tạo trực tuyến)
    changes: list[str]


class JobDraftRequest(BaseModel):
    """Thông tin nhà tuyển dụng đã nhập trên form, AI dựa vào đó viết nội dung tin."""
    title: str
    notes: str | None = None
    industry_id: int | None = Field(default=None, gt=0, le=2**63 - 1)
    province_id: int | None = Field(default=None, gt=0, le=2**63 - 1)
    employment_type: EmploymentType | None = None
    experience_level: ExperienceLevel | None = None
    salary_min: int | None = Field(default=None, ge=0, le=2**63 - 1)
    salary_max: int | None = Field(default=None, ge=0, le=2**63 - 1)
    positions: int | None = Field(default=None, ge=1, le=2**31 - 1)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = (value or "").strip()
        if not 5 <= len(value) <= 200:
            raise ValueError("Hãy nhập vị trí tuyển dụng từ 5 đến 200 ký tự")
        return value

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: str | None) -> str | None:
        value = (value or "").strip()
        if len(value) > DRAFT_NOTES_LIMIT:
            raise ValueError(f"Ý chính tối đa {DRAFT_NOTES_LIMIT} ký tự")
        return value or None


class JobDraftResponse(BaseModel):
    title: str
    description: str
    requirements: str
    benefits: str
