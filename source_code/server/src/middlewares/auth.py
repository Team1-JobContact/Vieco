from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.models.revoked_token import RevokedToken
from src.models.user import Role, User
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
    if not payload or "sub" not in payload or "jti" not in payload:
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
    user.role_name = role_name
    return user


def require_roles(*roles: str):
    """Phân quyền: chỉ cho phép các vai trò chỉ định truy cập, ví dụ require_roles("ADMIN")."""
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role_name not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn không có quyền truy cập")
        return user
    return checker
