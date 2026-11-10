"""Token JWT đã bị thu hồi khi đăng xuất (blacklist theo jti)."""
from sqlalchemy import Column, DateTime, String
from src.models.base import BaseModel


class RevokedToken(BaseModel):
    __tablename__ = "revoked_tokens"

    jti = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)  # quá hạn thì có thể dọn dẹp
