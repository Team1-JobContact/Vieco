"""Bong bóng chat hỏi đáp: lịch sử hội thoại do trình duyệt lưu và gửi lên mỗi lượt."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

USER_MESSAGE_LIMIT = 1000  # ký tự mỗi câu hỏi
ASSISTANT_MESSAGE_LIMIT = 6000  # câu trả lời cũ gửi lại làm ngữ cảnh
HISTORY_LIMIT = 40  # số tin nhắn tối đa trong một yêu cầu; máy chủ chỉ dùng các tin gần nhất


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

    @model_validator(mode="after")
    def check_content(self):
        self.content = self.content.strip()
        limit = USER_MESSAGE_LIMIT if self.role == "user" else ASSISTANT_MESSAGE_LIMIT
        if self.role == "user" and not self.content:
            raise ValueError("Hãy nhập câu hỏi")
        if len(self.content) > limit:
            raise ValueError(f"Mỗi câu hỏi tối đa {USER_MESSAGE_LIMIT} ký tự" if self.role == "user"
                             else "Tin nhắn trước đó quá dài")
        return self


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=HISTORY_LIMIT)
    page: str | None = None  # tiêu đề và đường dẫn trang người dùng đang xem

    @field_validator("messages")
    @classmethod
    def check_history(cls, messages):
        if messages[-1].role != "user":
            raise ValueError("Tin nhắn cuối cùng phải là câu hỏi của người dùng")
        return messages

    @field_validator("page")
    @classmethod
    def clip_page(cls, page):
        page = (page or "").strip()[:200]
        return page or None


class ChatResponse(BaseModel):
    reply: str


class ChatStatus(BaseModel):
    enabled: bool
