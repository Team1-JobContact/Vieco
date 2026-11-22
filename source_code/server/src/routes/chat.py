from fastapi import APIRouter
from src.controllers import chat_controller as controller
from src.schemas.chat import ChatResponse, ChatStatus

# Bong bóng chat hỏi đáp AI: dùng được cả khi chưa đăng nhập (giới hạn lượt theo IP).
router = APIRouter(prefix="/api/v1/chat", tags=["AI Chat"])
router.add_api_route("/status", controller.chat_status, methods=["GET"], response_model=ChatStatus)
router.add_api_route("", controller.chat, methods=["POST"], response_model=ChatResponse)
