"""Module M0: Danh mục và cấu hình."""
from sqlalchemy import Column, String, Text
from src.models.base import BaseModel, fk, flag


class Industry(BaseModel):
    __tablename__ = "industries"

    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(120), nullable=False, unique=True)
    is_active = flag(True)


class Skill(BaseModel):
    __tablename__ = "skills"

    name = Column(String(100), nullable=False, unique=True)
    industry_id = fk("industries.id", nullable=True)
    is_active = flag(True)


class Province(BaseModel):
    __tablename__ = "provinces"

    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(10), nullable=False, unique=True)
    is_active = flag(True)


class SystemSetting(BaseModel):
    __tablename__ = "system_settings"

    setting_key = Column(String(100), nullable=False, unique=True)
    setting_value = Column(Text, nullable=False)
    description = Column(String(255))


class StaticPage(BaseModel):
    __tablename__ = "static_pages"

    slug = Column(String(100), nullable=False, unique=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    is_published = flag(True)
