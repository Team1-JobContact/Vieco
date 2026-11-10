from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.revoked_token import RevokedToken
from src.models.user import Role, User
from src.schemas.auth import LoginRequest, RegisterRequest, UserResponse
from src.utils.security import create_access_token, hash_password, verify_password

MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_user_response(user: User, role_name: str) -> UserResponse:
    return UserResponse(
        id=user.id, email=user.email, full_name=user.full_name, phone=user.phone,
        role=role_name, is_email_verified=user.is_email_verified,
        status=user.status, created_at=user.created_at,
    )


def register_user(db: Session, data: RegisterRequest) -> UserResponse:
    email = data.email.lower()
    role = db.query(Role).filter(Role.name == data.role).first()
    if role is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "Chưa có dữ liệu vai trò, hãy chạy: python -m src.seeds.run")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã được đăng ký")
    user = User(email=email, password_hash=hash_password(data.password),
                role_id=role.id, full_name=data.full_name, phone=data.phone)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # hai request đăng ký trùng email cùng lúc
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã được đăng ký")
    db.refresh(user)
    return to_user_response(user, role.name)


def login_user(db: Session, data: LoginRequest) -> tuple[UserResponse, str]:
    user = db.query(User).filter(User.email == data.email.lower()).first()
    invalid = HTTPException(status.HTTP_401_UNAUTHORIZED, "Email hoặc mật khẩu không đúng")
    if user is None:
        raise invalid

    now = _utcnow()
    if user.status == "LOCKED":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tài khoản đã bị khóa")
    if user.locked_until and user.locked_until > now:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            "Đăng nhập sai nhiều lần, vui lòng thử lại sau ít phút")

    if not verify_password(data.password, user.password_hash):
        user.failed_login_count = (user.failed_login_count or 0) + 1
        if user.failed_login_count >= MAX_FAILED_LOGINS:
            user.locked_until = now + timedelta(minutes=LOCK_MINUTES)
            user.failed_login_count = 0
        db.commit()
        raise invalid

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    db.commit()
    db.refresh(user)

    role_name = db.query(Role.name).filter(Role.id == user.role_id).scalar()
    return to_user_response(user, role_name), create_access_token(user.id, role_name)


def revoke_token(db: Session, jti: str, exp: int) -> None:
    if db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
        return
    expires_at = datetime.fromtimestamp(exp, timezone.utc).replace(tzinfo=None)
    db.add(RevokedToken(jti=jti, expires_at=expires_at))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
