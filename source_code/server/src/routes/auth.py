from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middlewares.auth import get_current_user, get_token_payload
from src.models.user import User
from src.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.services import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return auth_service.register_user(db, data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user, token = auth_service.login_user(db, data)
    return TokenResponse(access_token=token, user=user)


@router.post("/logout")
def logout(payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)):
    auth_service.revoke_token(db, payload["jti"], payload["exp"])
    return {"status": "success", "message": "Đăng xuất thành công"}


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return auth_service.to_user_response(user, user.role_name)
