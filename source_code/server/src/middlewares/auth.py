from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.models.revoked_token import RevokedToken
from datetime import datetime, timezone
from src.models.user import PasswordReset, Role, User
from src.utils.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Chưa đăng nhập hoặc token không hợp lệ",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    payload = decode_access_token(credentials.credentials)
    if not payload or not isinstance(payload.get("jti"), str) or not payload["jti"]:
        raise unauthorized
    try:
        if int(payload["sub"]) <= 0:
            raise ValueError
        datetime.fromtimestamp(payload["exp"], timezone.utc)
        datetime.fromtimestamp(payload["iat"], timezone.utc)
    except (KeyError, ValueError, TypeError, OverflowError, OSError):
        raise unauthorized
    if db.query(RevokedToken).filter(RevokedToken.jti == payload["jti"]).first():
        raise unauthorized
    return payload


def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> User:
    """Trả về User hiện tại; gắn thêm thuộc tính `role_name` (ADMIN/CANDIDATE/EMPLOYER)."""
    row = (
        db.query(User, Role.name)
        .join(Role, Role.id == User.role_id)
        .filter(User.id == int(payload["sub"]))
        .first()
    )
    if row is None or row[0].status != "ACTIVE":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tài khoản không tồn tại hoặc đã bị khóa")
    user, role_name = row
    reset = db.query(PasswordReset.used_at).filter(
        PasswordReset.user_id == user.id, PasswordReset.used_at.is_not(None)
    ).order_by(PasswordReset.used_at.desc()).first()
    if reset and datetime.fromtimestamp(payload.get("iat", 0), timezone.utc).replace(tzinfo=None) <= reset[0]:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Mật khẩu đã đổi, vui lòng đăng nhập lại")
    user.role_name = role_name
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Cho API công khai: trả về User nếu token hợp lệ, ngược lại coi là khách (None) thay vì báo 401."""
    if credentials is None:
        return None
    try:
        return get_current_user(get_token_payload(credentials, db), db)
    except HTTPException:
        return None


def require_roles(*roles: str):
    """Phân quyền: chỉ cho phép các vai trò chỉ định truy cập, ví dụ require_roles("ADMIN")."""
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role_name not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn không có quyền truy cập")
        return user
    return checker
