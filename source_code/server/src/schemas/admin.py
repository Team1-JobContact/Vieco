from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.design import CategoryCreate


class UserStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ACTIVE", "LOCKED"]


class CategoryUpdate(CategoryCreate):
    model_config = ConfigDict(extra="forbid")
    is_active: bool = True


class PageUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=50000)
    is_published: bool


class UploadSettingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    value: str = Field(min_length=1, max_length=100)
