"""Tạo nội dung CV bằng AI (Claude) từ thông tin ứng viên tự nhập.

- Bật khi server/.env có ANTHROPIC_API_KEY. Thiếu khóa hoặc chưa cài thư viện anthropic thì API trả 503,
  các phần khác của trình tạo CV vẫn dùng bình thường.
- Claude trả về JSON theo schema cố định (structured outputs); kết quả được cắt theo giới hạn của
  CVContent rồi mới trả cho trình duyệt. Người dùng xem lại và chỉnh sửa trước khi lưu.
- Mỗi tài khoản tối đa HOURLY_LIMIT lượt mỗi giờ để giới hạn chi phí (đếm trong bộ nhớ của tiến trình).
"""
import json
import logging
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status

from src.config.settings import settings
from src.schemas.cv_builder import (
    ENTRY_LIMITS, LIST_LIMITS, PERSONAL_LIMITS, SECTION_LIMITS, SUMMARY_LIMIT, CVContent,
)

logger = logging.getLogger(__name__)

HOURLY_LIMIT = 10
REQUEST_TIMEOUT_SECONDS = 90
_calls: dict[int, deque] = defaultdict(deque)
_calls_lock = threading.Lock()

SYSTEM_PROMPT = """Bạn là chuyên gia tuyển dụng, giúp ứng viên Việt Nam viết CV xin việc. Từ thông tin ứng viên tự nhập \
(có thể lộn xộn, viết tắt hoặc thiếu dấu), hãy sắp xếp thành một CV rõ ràng, chuyên nghiệp theo JSON schema được yêu cầu.

Nguyên tắc:
- Chỉ dùng thông tin ứng viên cung cấp. Không bịa thêm công ty, trường học, thời gian, số liệu, chứng chỉ hay thông tin \
liên hệ. Thiếu thông tin thì để chuỗi rỗng hoặc mảng rỗng.
- Được diễn đạt lại cho chuyên nghiệp, sửa chính tả, thêm dấu tiếng Việt, gộp ý trùng và đưa từng thông tin vào đúng mục.
- Viết bằng tiếng Việt, trừ khi ứng viên viết toàn bộ bằng tiếng Anh hoặc yêu cầu CV tiếng Anh.
- summary: 2-4 câu về điểm mạnh và mục tiêu nghề nghiệp, gắn với vị trí ứng tuyển nếu có.
- description: mỗi ý một dòng (ngăn cách bằng \\n), bắt đầu bằng động từ, không thêm ký hiệu đầu dòng; giữ nguyên các con số \
ứng viên đã nêu.
- Thời gian dạng MM/YYYY hoặc YYYY; việc đang làm hoặc đang học thì end là "Hiện tại".
- Kinh nghiệm, học vấn, dự án, hoạt động xếp từ mới nhất đến cũ nhất.
- skills, languages, certificates, interests: mỗi phần tử ngắn gọn, ví dụ "SQL", "Tiếng Anh - IELTS 7.0", \
"Google Analytics Certification (2023)"."""


def _entries(description: str) -> dict:
    return {"type": "array", "description": description, "items": {"$ref": "#/$defs/entry"}}


def _strings(description: str) -> dict:
    return {"type": "array", "description": description, "items": {"type": "string"}}


def _object(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


OUTPUT_SCHEMA = {
    **_object({
        "personal": _object({
            "full_name": {"type": "string", "description": "Họ và tên"},
            "title": {"type": "string", "description": "Vị trí ứng tuyển hoặc chức danh nghề nghiệp"},
            "birthday": {"type": "string", "description": "Ngày sinh, ví dụ 15/08/2001"},
            "phone": {"type": "string"},
            "email": {"type": "string"},
            "address": {"type": "string", "description": "Địa chỉ hoặc tỉnh/thành phố"},
            "link": {"type": "string", "description": "Website, LinkedIn, GitHub hoặc portfolio"},
        }),
        "summary": {"type": "string", "description": "Giới thiệu bản thân và mục tiêu nghề nghiệp"},
        "experience": _entries("Kinh nghiệm làm việc, kể cả thực tập và làm thêm: title = chức danh, subtitle = tên công ty"),
        "education": _entries("Học vấn: title = tên trường, subtitle = chuyên ngành, bằng cấp hoặc xếp loại"),
        "projects": _entries("Dự án: title = tên dự án, subtitle = vai trò hoặc công nghệ chính"),
        "activities": _entries("Hoạt động ngoại khóa, tình nguyện, câu lạc bộ: title = tên hoạt động hoặc tổ chức, subtitle = vai trò"),
        "skills": _strings("Kỹ năng chuyên môn và kỹ năng mềm"),
        "languages": _strings("Ngoại ngữ kèm trình độ hoặc chứng chỉ"),
        "certificates": _strings("Chứng chỉ, giải thưởng, danh hiệu, kèm năm nếu có"),
        "interests": _strings("Sở thích"),
    }),
    "$defs": {"entry": _object({
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "start": {"type": "string", "description": "MM/YYYY hoặc YYYY"},
        "end": {"type": "string", "description": "MM/YYYY, YYYY hoặc Hiện tại"},
        "description": {"type": "string", "description": "Mỗi ý một dòng"},
    })},
}


def _clip(value, limit: int) -> str:
    return value.strip()[:limit].strip() if isinstance(value, str) else ""


def _clip_content(raw) -> dict:
    """Ép kết quả AI về đúng cấu trúc và cắt theo giới hạn, để không bao giờ trả lỗi chỉ vì AI viết dài."""
    raw = raw if isinstance(raw, dict) else {}
    personal = raw.get("personal") if isinstance(raw.get("personal"), dict) else {}
    data = {
        "personal": {key: _clip(personal.get(key), limit) for key, limit in PERSONAL_LIMITS.items()},
        "summary": _clip(raw.get("summary"), SUMMARY_LIMIT),
    }
    for section, max_items in SECTION_LIMITS.items():
        items = raw.get(section) if isinstance(raw.get(section), list) else []
        entries = [{key: _clip(item.get(key), limit) for key, limit in ENTRY_LIMITS.items()}
                   for item in items if isinstance(item, dict)]
        data[section] = [entry for entry in entries if any(entry.values())][:max_items]
    for section, (max_items, limit) in LIST_LIMITS.items():
        items = raw.get(section) if isinstance(raw.get(section), list) else []
        data[section] = [text for text in (_clip(item, limit) for item in items) if text][:max_items]
    return data


def _take_quota(user_id: int) -> None:
    now = time.monotonic()
    with _calls_lock:
        calls = _calls[user_id]
        while calls and now - calls[0] > 3600:
            calls.popleft()
        if len(calls) >= HOURLY_LIMIT:
            minutes = max(1, int((3600 - (now - calls[0])) // 60) + 1)
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                                f"Mỗi giờ chỉ tạo CV bằng AI được {HOURLY_LIMIT} lần, vui lòng thử lại sau {minutes} phút")
        calls.append(now)


def _prompt(text: str, target: str | None) -> str:
    return (f"Vị trí muốn ứng tuyển: {target or '(ứng viên không nêu)'}\n\n"
            f"Thông tin ứng viên tự nhập:\n<thong_tin_ung_vien>\n{text}\n</thong_tin_ung_vien>")


def _create_message(prompt: str):
    """Gọi Claude. Tách riêng để kiểm thử thay bằng phản hồi giả, không gọi mạng."""
    try:
        import anthropic
    except ImportError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Máy chủ chưa cài thư viện anthropic, hãy chạy pip install -r requirements.txt")
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=REQUEST_TIMEOUT_SECONDS, max_retries=1)
    try:
        return client.beta.messages.create(
            model=settings.AI_CV_MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",  # bị bộ lọc an toàn từ chối thì máy chủ Anthropic tự chạy lại bằng model dự phòng
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as error:
        logger.error("Claude từ chối khóa API (%s)", error.status_code)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Khóa API của dịch vụ AI không hợp lệ, hãy báo quản trị viên kiểm tra ANTHROPIC_API_KEY")
    except anthropic.RateLimitError:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Dịch vụ AI đang bận, vui lòng thử lại sau ít phút")
    except anthropic.APITimeoutError:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "AI phản hồi quá lâu, vui lòng thử lại")
    except anthropic.APIConnectionError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Máy chủ không kết nối được dịch vụ AI, vui lòng thử lại sau")
    except anthropic.APIStatusError as error:
        logger.error("Claude trả lỗi %s (request id %s): %s", error.status_code, error.request_id, error.message)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE if error.status_code >= 500 else status.HTTP_502_BAD_GATEWAY,
                            "Dịch vụ AI tạm thời không tạo được CV, vui lòng thử lại sau")


def _output_text(response) -> str:
    """Nội dung JSON của model trả lời cuối cùng (bỏ phần của model đã từ chối trước khối fallback, nếu có)."""
    blocks = list(response.content or [])
    start = max((i + 1 for i, block in enumerate(blocks) if block.type == "fallback"), default=0)
    return "".join(block.text for block in blocks[start:] if block.type == "text")


def generate(user, text: str, target: str | None) -> dict:
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Tính năng tạo CV bằng AI chưa được bật trên máy chủ (thiếu ANTHROPIC_API_KEY)")
    _take_quota(user.id)
    response = _create_message(_prompt(text, target))
    if response.stop_reason == "refusal":
        raise HTTPException(422,
                            "AI không thể xử lý nội dung này, hãy kiểm tra lại thông tin bạn nhập")
    if response.stop_reason == "max_tokens":
        raise HTTPException(422,
                            "Thông tin quá dài để AI xử lý trong một lần, hãy rút gọn bớt")
    try:
        raw = json.loads(_output_text(response))
    except ValueError:
        logger.error("Claude trả về JSON không hợp lệ (stop_reason=%s)", response.stop_reason)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "AI trả về dữ liệu không hợp lệ, vui lòng thử lại")
    return CVContent.model_validate(_clip_content(raw)).model_dump()
