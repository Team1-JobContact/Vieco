"""Request contracts for the core architecture API."""
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator
from src.schemas.auth import RegisterRequest

class EmailRequest(BaseModel):
    email: EmailStr

class TokenRequest(BaseModel):
    token: str = Field(min_length=20, max_length=255)

class ResetPasswordRequest(TokenRequest):
    password: str
    _password = field_validator("password")(RegisterRequest.validate_password.__func__)

class ApprovalRequest(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def require_reason(self):
        if self.reason is not None:
            self.reason = self.reason.strip()
        if self.status == "REJECTED" and (not self.reason or len(self.reason) < 10):
            raise ValueError("Lý do từ chối phải từ 10 đến 500 ký tự")
        return self

class CategoryCreate(BaseModel):
    type: Literal["industries", "skills", "provinces"]
    name: str = Field(min_length=1, max_length=100)
    code: str | None = Field(default=None, min_length=1, max_length=10)
    industry_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_category(self):
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Tên danh mục không được để trống")
        if self.type == "provinces":
            self.code = (self.code or "").strip()
            if not self.code:
                raise ValueError("Tỉnh/thành phải có mã code")
        elif self.code is not None:
            raise ValueError("code chỉ dùng cho tỉnh/thành")
        if self.type != "skills" and self.industry_id is not None:
            raise ValueError("industry_id chỉ dùng cho kỹ năng")
        return self

class ApplicationCreate(BaseModel):
    job_id: int = Field(gt=0)
    cv_id: int = Field(gt=0)
    cover_letter: str | None = Field(default=None, max_length=5000)

class ApplicationStatusUpdate(BaseModel):
    status: Literal["VIEWED", "INTERVIEW", "ACCEPTED", "REJECTED"]
    note: str | None = Field(default=None, max_length=500)
