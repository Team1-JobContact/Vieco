from fastapi import BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middlewares.auth import get_current_user, get_token_payload
from src.models.user import User
from src.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.services import auth_service



def register(data: RegisterRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    response = auth_service.register_user(db, data)
    from src.services import email_service
    user = db.get(User, response.id)
    raw = email_service.issue_verification(db, user)
    if raw:
        def deliver():
            try:
                email_service._deliver(response.email, "verify-email", raw)
            except Exception:
                import logging
                logging.getLogger(__name__).error("Verification email delivery failed")
        background_tasks.add_task(deliver)
    return response


def login(data: LoginRequest, db: Session = Depends(get_db)):
    user, token = auth_service.login_user(db, data)
    return TokenResponse(access_token=token, user=user)


def logout(payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)):
    auth_service.revoke_token(db, payload["jti"], payload["exp"])
    return {"status": "success", "message": "Đăng xuất thành công"}


def me(user: User = Depends(get_current_user)):
    return auth_service.to_user_response(user, user.role_name)
