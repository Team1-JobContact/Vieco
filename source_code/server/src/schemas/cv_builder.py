"""Trình tạo CV trực tuyến: nội dung CV lưu kèm tệp PDF và yêu cầu tạo CV bằng AI.

Giới hạn độ dài khai báo một lần ở đây, dùng chung cho kiểm tra dữ liệu người dùng gửi lên
và cho việc cắt gọn kết quả AI (cv_ai_service).
"""
import base64
import binascii
import re
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, field_validator, model_validator

from src.schemas.candidate import CVResponse

Template = Literal["elegant", "modern", "minimal"]  # Thanh lịch, Hiện đại, Tối giản

PERSONAL_LIMITS = {"full_name": 150, "title": 150, "birthday": 30, "phone": 30, "email": 254, "address": 255, "link": 255}
ENTRY_LIMITS = {"title": 200, "subtitle": 200, "start": 30, "end": 30, "description": 3000}
SUMMARY_LIMIT = 3000
# Mục có nhiều dòng thông tin (thời gian, mô tả): số mục tối đa.
SECTION_LIMITS = {"experience": 15, "education": 10, "projects": 10, "activities": 10}
# Mục dạng danh sách ngắn: (số mục tối đa, số ký tự tối đa mỗi mục).
LIST_LIMITS = {"skills": (40, 100), "languages": (10, 100), "certificates": (20, 200), "interests": (15, 100)}

PHOTO_MAX_BYTES = 300 * 1024
PHOTO_PATTERN = re.compile(r"data:image/(jpeg|png|webp);base64,([A-Za-z0-9+/]+={0,2})")
PHOTO_MAGIC = {"jpeg": b"\xff\xd8\xff", "png": b"\x89PNG\r\n\x1a\n", "webp": b"RIFF"}


def _empty_if_none(value):
    return "" if value is None else value


def _text(limit: int, label: str):
    def check(value: str) -> str:
        value = value.strip()
        if len(value) > limit:
            raise ValueError(f"{label} tối đa {limit} ký tự")
        return value
    return Annotated[str, BeforeValidator(_empty_if_none), AfterValidator(check)]


def _items(item_type, limit: int, label: str):
    def check(items: list) -> list:
        items = [item for item in items if (any(item.model_dump().values()) if isinstance(item, BaseModel) else item)]
        if len(items) > limit:
            raise ValueError(f"{label} tối đa {limit} mục")
        return items
    return Annotated[list[item_type], BeforeValidator(lambda v: [] if v is None else v), AfterValidator(check)]


class CVEntry(BaseModel):
    """Một mục kinh nghiệm, học vấn, dự án hoặc hoạt động.

    title/subtitle theo từng mục: chức danh/công ty, trường/chuyên ngành, tên dự án/vai trò, hoạt động/vai trò.
    description: mỗi dòng là một ý.
    """
    model_config = ConfigDict(extra="ignore")

    title: _text(ENTRY_LIMITS["title"], "Tên mục") = ""
    subtitle: _text(ENTRY_LIMITS["subtitle"], "Dòng mô tả ngắn") = ""
    start: _text(ENTRY_LIMITS["start"], "Thời gian bắt đầu") = ""
    end: _text(ENTRY_LIMITS["end"], "Thời gian kết thúc") = ""
    description: _text(ENTRY_LIMITS["description"], "Mô tả chi tiết") = ""


class CVPersonal(BaseModel):
    model_config = ConfigDict(extra="ignore")

    full_name: _text(PERSONAL_LIMITS["full_name"], "Họ và tên") = ""
    title: _text(PERSONAL_LIMITS["title"], "Vị trí ứng tuyển") = ""
    birthday: _text(PERSONAL_LIMITS["birthday"], "Ngày sinh") = ""
    phone: _text(PERSONAL_LIMITS["phone"], "Số điện thoại") = ""
    email: _text(PERSONAL_LIMITS["email"], "Email") = ""
    address: _text(PERSONAL_LIMITS["address"], "Địa chỉ") = ""
    link: _text(PERSONAL_LIMITS["link"], "Website") = ""


class CVContent(BaseModel):
    """Phần nội dung của CV (AI tạo được phần này; ảnh và mẫu do người dùng chọn)."""
    model_config = ConfigDict(extra="ignore")

    personal: CVPersonal = Field(default_factory=CVPersonal)
    summary: _text(SUMMARY_LIMIT, "Giới thiệu bản thân") = ""
    experience: _items(CVEntry, SECTION_LIMITS["experience"], "Kinh nghiệm làm việc") = []
    education: _items(CVEntry, SECTION_LIMITS["education"], "Học vấn") = []
    projects: _items(CVEntry, SECTION_LIMITS["projects"], "Dự án") = []
    activities: _items(CVEntry, SECTION_LIMITS["activities"], "Hoạt động") = []
    skills: _items(_text(LIST_LIMITS["skills"][1], "Mỗi kỹ năng"), LIST_LIMITS["skills"][0], "Kỹ năng") = []
    languages: _items(_text(LIST_LIMITS["languages"][1], "Mỗi ngoại ngữ"), LIST_LIMITS["languages"][0], "Ngoại ngữ") = []
    certificates: _items(_text(LIST_LIMITS["certificates"][1], "Mỗi chứng chỉ"), LIST_LIMITS["certificates"][0], "Chứng chỉ & giải thưởng") = []
    interests: _items(_text(LIST_LIMITS["interests"][1], "Mỗi sở thích"), LIST_LIMITS["interests"][0], "Sở thích") = []


class CVBuilderData(CVContent):
    """Dữ liệu trình tạo CV lưu cùng tệp PDF để mở lại và chỉnh sửa."""
    version: Literal[1] = 1
    template: Template = "elegant"
    photo: str | None = None  # data URL JPG/PNG/WEBP, ảnh 3x4 đã được trình duyệt thu nhỏ

    @field_validator("photo")
    @classmethod
    def validate_photo(cls, value: str | None) -> str | None:
        if not value:
            return None
        match = PHOTO_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError("Ảnh CV phải là ảnh JPG, PNG hoặc WEBP")
        try:
            raw = base64.b64decode(match.group(2), validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("Ảnh CV bị hỏng, hãy chọn ảnh khác")
        if len(raw) > PHOTO_MAX_BYTES:
            raise ValueError(f"Ảnh CV tối đa {PHOTO_MAX_BYTES // 1024} KB")
        kind = match.group(1)
        if not raw.startswith(PHOTO_MAGIC[kind]) or (kind == "webp" and raw[8:12] != b"WEBP"):
            raise ValueError("Ảnh CV bị hỏng, hãy chọn ảnh khác")
        return value

    @model_validator(mode="after")
    def require_name(self):
        if not self.personal.full_name:
            raise ValueError("Hãy nhập họ và tên trước khi lưu CV")
        return self


class CVBuilderResponse(BaseModel):
    cv: CVResponse
    data: dict


class CVAIRequest(BaseModel):
    text: str
    target: str | None = None  # vị trí muốn ứng tuyển

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 30:
            raise ValueError("Hãy nhập ít nhất 30 ký tự thông tin về bản thân để AI tạo CV")
        if len(value) > 8000:
            raise ValueError("Thông tin tối đa 8000 ký tự")
        return value

    @field_validator("target")
    @classmethod
    def validate_target(cls, value: str | None) -> str | None:
        value = (value or "").strip()
        if len(value) > 150:
            raise ValueError("Vị trí ứng tuyển tối đa 150 ký tự")
        return value or None


class CVAIResponse(BaseModel):
    data: CVContent
