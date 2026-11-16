from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EducationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    school_name: str = Field(min_length=1, max_length=200)
    major: str | None = Field(default=None, max_length=150)
    degree: str | None = Field(default=None, max_length=50)
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Ngày kết thúc phải từ ngày bắt đầu trở đi")
        return self


class ExperienceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    company_name: str = Field(min_length=1, max_length=200)
    position: str = Field(min_length=1, max_length=150)
    start_date: date
    end_date: date | None = None
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("Ngày kết thúc phải từ ngày bắt đầu trở đi")
        return self


class SkillInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skill_id: int = Field(gt=0)
    level: Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"] | None = None
