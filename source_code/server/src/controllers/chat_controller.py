from fastapi import Depends, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middlewares.auth import get_optional_user
from src.models.user import User
from src.schemas.chat import ChatRequest, ChatResponse, ChatStatus
from src.services import chat_service


def _client_ip(request: Request) -> str:
    """IP người dùng; sau proxy (Render) lấy địa chỉ đầu tiên trong X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    return forwarded or (request.client.host if request.client else "unknown")


def chat_status():
    return ChatStatus(enabled=chat_service.enabled())


def chat(data: ChatRequest, request: Request, user: User | None = Depends(get_optional_user),
         db: Session = Depends(get_db)):
    client_key = f"user:{user.id}" if user else f"ip:{_client_ip(request)}"
    return ChatResponse(reply=chat_service.reply(db, user, client_key, data.messages, data.page))
