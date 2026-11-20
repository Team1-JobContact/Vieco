"""Lớp nền chung cho mọi model: id, created_at, updated_at (theo mục 1.2 tài liệu thiết kế)."""
from datetime import timezone

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, func, true, false,
)
from sqlalchemy.types import TypeDecorator
from src.config import database
from src.config.database import Base

# BIGINT tự tăng trên MySQL/PostgreSQL; SQLite (nếu dùng để test) chỉ tự tăng với INTEGER.
BigInt = BigInteger().with_variant(Integer, "sqlite")


class ServerTimestamp(TypeDecorator):
    """Label database-generated dates with their clock, including existing rows."""
    impl = DateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is None or value.tzinfo is not None:
            return value
        zone = database.SERVER_TIMEZONE if dialect.name == "mysql" else timezone.utc
        return value.replace(tzinfo=zone)

    def process_bind_param(self, value, dialect):
        if value is None or value.tzinfo is None:
            return value
        zone = database.SERVER_TIMEZONE if dialect.name == "mysql" else timezone.utc
        return value.astimezone(zone).replace(tzinfo=None)


class BaseModel(Base):
    __abstract__ = True

    id = Column(BigInt, primary_key=True, autoincrement=True)
    created_at = Column(ServerTimestamp(), nullable=False, server_default=func.now())
    updated_at = Column(ServerTimestamp(), nullable=False, server_default=func.now(), onupdate=func.now())


def fk(target: str, nullable: bool = False, ondelete: str | None = None, **kwargs) -> Column:
    """Cột khóa ngoại BIGINT trỏ tới <target> (dạng 'bang.id')."""
    return Column(BigInt, ForeignKey(target, ondelete=ondelete), nullable=nullable, **kwargs)


def flag(default: bool) -> Column:
    """Cột BOOLEAN NOT NULL với giá trị mặc định ở cả ORM lẫn CSDL."""
    return Column(Boolean, nullable=False, default=default,
                  server_default=true() if default else false())


def in_check(column: str, values, name: str) -> CheckConstraint:
    """CHECK (column IN (...)) cho các trường trạng thái/enum dạng VARCHAR."""
    items = ", ".join(f"'{v}'" for v in values)
    return CheckConstraint(f"{column} IN ({items})", name=name)
