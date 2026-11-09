"""Module M1: Vai trò, tài khoản, mã xác thực email, mã đặt lại mật khẩu."""
from sqlalchemy import Column, DateTime, Integer, String, text
from src.models.base import BaseModel, fk, flag, in_check
from src.models.enums import USER_STATUSES


class Role(BaseModel):
    __tablename__ = "roles"

    name = Column(String(30), nullable=False, unique=True)  # ADMIN, CANDIDATE, EMPLOYER
    description = Column(String(255))


class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = (in_check("status", USER_STATUSES, "status"),)

    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role_id = fk("roles.id")
    full_name = Column(String(150), nullable=False)
    phone = Column(String(20))
    avatar_url = Column(String(500))
    is_email_verified = flag(False)
    status = Column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    failed_login_count = Column(Integer, nullable=False, default=0, server_default=text("0"))
    locked_until = Column(DateTime)
    last_login_at = Column(DateTime)


class EmailVerification(BaseModel):
    __tablename__ = "email_verifications"

    user_id = fk("users.id", ondelete="CASCADE")
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)


class PasswordReset(BaseModel):
    __tablename__ = "password_resets"

    user_id = fk("users.id", ondelete="CASCADE")
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)
