"""Bong bóng chat AI: API công khai, công cụ chỉ đọc dữ liệu công khai, vòng gọi công cụ và giới hạn lượt."""
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.config.settings import settings
from src.models import Company, Industry, Job, Province, Role, StaticPage, User
from src.services import chat_service
from src.services.public_service import today
from src.utils.security import hash_password

URL = "/api/v1/chat"


@pytest.fixture(autouse=True)
def reset_quota():
    chat_service._calls.clear()
    chat_service._all_calls.clear()
    yield
    chat_service._calls.clear()
    chat_service._all_calls.clear()


@pytest.fixture()
def data(db_session):
    s = db_session
    owner = User(email="hr@example.com", password_hash=hash_password("Abcd1234"),
                 role_id=s.query(Role.id).filter(Role.name == "EMPLOYER").scalar(), full_name="HR")
    it = Industry(name="Công nghệ thông tin", slug="cntt")
    hcm, hn = Province(name="TP. Hồ Chí Minh", code="HCM"), Province(name="Hà Nội", code="HN")
    acme = Company(name="Acme Việt Nam", slug="acme", status="APPROVED", description="Công ty phần mềm.",
                   industry_id=None)
    pending = Company(name="Pending Co", slug="pending", status="PENDING")
    s.add_all([owner, it, hcm, hn, acme, pending])
    s.flush()

    def job(title, company, **kw):
        values = dict(company_id=company.id, created_by=owner.id, title=title, status="APPROVED",
                      deadline=today() + timedelta(days=10),
                      published_at=datetime.now(timezone.utc).replace(tzinfo=None),
                      industry_id=it.id, province_id=hcm.id, salary_min=15_000_000, salary_max=25_500_000,
                      employment_type="FULL_TIME", experience_level="FROM_1_TO_3",
                      description="Phát triển giao diện React.", requirements="1 năm React.")
        values.update(kw)
        row = Job(**values)
        s.add(row)
        s.flush()
        return row

    jobs = {
        "react": job("Frontend React Developer", acme),
        "hn": job("Kế toán tổng hợp", acme, province_id=hn.id, salary_min=None, salary_max=None),
        "draft": job("Hidden Draft React", acme, status="DRAFT"),
        "expired": job("Hidden Expired React", acme, deadline=today() - timedelta(days=1)),
        "pending": job("Hidden Pending Company React", pending),
    }
    s.add_all([StaticPage(slug="faq", title="Câu hỏi thường gặp", content="Hỏi: Ứng tuyển thế nào? Đáp: ..."),
               StaticPage(slug="dieu-khoan", title="Điều khoản", content="...", is_published=False)])
    s.commit()
    return SimpleNamespace(jobs=jobs, acme=acme, pending=pending)


def tool(db, name, args):
    content, is_error = chat_service.run_tool(db, name, args)
    return (content if is_error else json.loads(content)), is_error


def text_response(text, stop_reason="end_turn"):
    return SimpleNamespace(stop_reason=stop_reason, content=[
        SimpleNamespace(type="thinking", thinking="", signature="sig"), SimpleNamespace(type="text", text=text)])


def tool_response(*calls):
    return SimpleNamespace(stop_reason="tool_use", content=[
        SimpleNamespace(type="tool_use", id=f"call_{i}", name=name, input=args) for i, (name, args) in enumerate(calls)])


@pytest.fixture()
def ai(monkeypatch):
    """Thay lời gọi Claude bằng chuỗi phản hồi giả; ghi lại mọi yêu cầu gửi đi."""
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "sk-test")
    state = {"responses": [], "requests": []}

    def create(system, messages, final):
        state["requests"].append({"system": system, "messages": [dict(m) for m in messages], "final": final})
        return state["responses"].pop(0) if len(state["responses"]) > 1 else state["responses"][0]
    monkeypatch.setattr(chat_service, "_create_message", create)
    return state


def ask(client, text="Có việc React nào ở TP.HCM không?", headers=None, history=(), **extra):
    messages = [*history, {"role": "user", "content": text}]
    return client.post(URL, json={"messages": messages, **extra}, headers=headers or {})


def make_user(client, email="cand@example.com", role="CANDIDATE"):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "Abcd1234", "full_name": "Nguyen Van A", "role": role})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Abcd1234"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_status_and_disabled_without_key(client, monkeypatch):
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
    assert client.get(f"{URL}/status").json() == {"enabled": False}
    r = ask(client)
    assert r.status_code == 503 and "ANTHROPIC_API_KEY" in r.json()["detail"]
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "sk-test")
    assert client.get(f"{URL}/status").json() == {"enabled": True}


def test_request_validation(client, ai):
    ai["responses"] = [text_response("ok")]
    assert ask(client, "   ").status_code == 422
    r = ask(client, "x" * 1001)
    assert r.status_code == 422 and "1000 ký tự" in r.json()["detail"][0]["msg"]
    r = client.post(URL, json={"messages": [{"role": "user", "content": "Chào"}, {"role": "assistant", "content": "Chào bạn"}]})
    assert r.status_code == 422 and "câu hỏi của người dùng" in r.json()["detail"][0]["msg"]
    assert client.post(URL, json={"messages": [{"role": "user", "content": "a"}] * 41}).status_code == 422
    assert client.post(URL, json={"messages": [{"role": "system", "content": "a"}]}).status_code == 422
    assert ai["requests"] == []


def test_tool_loop_answers_with_public_jobs(client, data, ai):
    ai["responses"] = [tool_response(("search_jobs", {"keyword": "React", "province": "TP.HCM"})),
                       text_response("Có 1 việc: [Frontend React Developer](pages/job.html?id=1)")]
    history = [{"role": "assistant", "content": "Xin chào!"}, {"role": "user", "content": "Chào"},
               {"role": "user", "content": "Mình tìm việc"}, {"role": "assistant", "content": "Bạn muốn làm gì?"}]
    r = ask(client, history=history, page="Việc làm | Vieco — pages/jobs.html")
    assert r.status_code == 200, r.text
    assert r.json()["reply"].startswith("Có 1 việc")

    first, second = ai["requests"]
    assert first["final"] is False
    # Bỏ tin chào của trợ lý ở đầu, gộp hai câu hỏi liên tiếp.
    assert [m["role"] for m in first["messages"]] == ["user", "assistant", "user"]
    assert first["messages"][0]["content"] == "Chào\n\nMình tìm việc"
    context = first["system"][1]["text"]
    assert "khách chưa đăng nhập" in context and "pages/jobs.html" in context
    assert first["system"][0]["cache_control"] == {"type": "ephemeral"}

    tool_turn = second["messages"][-1]["content"][0]
    assert tool_turn["tool_use_id"] == "call_0" and tool_turn["is_error"] is False
    result = json.loads(tool_turn["content"])
    assert result["total"] == 1
    job = result["jobs"][0]
    assert job["title"] == "Frontend React Developer" and job["company"] == "Acme Việt Nam"
    assert job["salary"] == "15 – 25,5 triệu" and job["url"] == f"pages/job.html?id={data.jobs['react'].id}"
    assert second["messages"][-2]["role"] == "assistant"  # nội dung gốc của Claude (kể cả thinking) được gửi lại


def test_logged_in_role_in_context(client, ai):
    ai["responses"] = [text_response("Chào bạn")]
    assert ask(client, "Chào", headers=make_user(client)).status_code == 200
    assert "ứng viên đã đăng nhập" in ai["requests"][0]["system"][1]["text"]
    # Token sai vẫn dùng được như khách, không bị 401.
    assert ask(client, "Chào", headers={"Authorization": "Bearer sai"}).status_code == 200
    assert "khách chưa đăng nhập" in ai["requests"][1]["system"][1]["text"]


def test_tools_only_read_public_data(db_session, data):
    s = db_session
    result, err = tool(s, "search_jobs", {"keyword": "React"})
    assert not err and [j["title"] for j in result["jobs"]] == ["Frontend React Developer"]
    result, err = tool(s, "search_jobs", {"province": "Sài Gòn"})
    assert not err and result["total"] == 1
    result, err = tool(s, "search_jobs", {"province": "ha noi", "industry": "công nghệ"})
    assert not err and result["jobs"][0]["title"] == "Kế toán tổng hợp" and result["jobs"][0]["salary"] == "Thỏa thuận"
    result, err = tool(s, "search_jobs", {"province": "Paris"})
    assert err and "Hà Nội" in result and "TP. Hồ Chí Minh" in result
    result, err = tool(s, "search_jobs", {"limit": "nhiều"})
    assert err and "Tham số không hợp lệ" in result

    react = data.jobs["react"]
    result, err = tool(s, "get_job", {"job_id": react.id})
    assert not err and result["description"] == "Phát triển giao diện React." and result["requirements"] == "1 năm React."
    s.refresh(react)
    assert react.view_count == 0  # trợ lý đọc tin không tính là lượt xem
    for hidden in ("draft", "expired", "pending"):
        result, err = tool(s, "get_job", {"job_id": data.jobs[hidden].id})
        assert err and "Không tìm thấy" in result

    result, err = tool(s, "search_companies", {})
    assert not err and [c["name"] for c in result["companies"]] == ["Acme Việt Nam"]
    result, err = tool(s, "get_company", {"company_id": data.acme.id})
    assert not err and result["open_jobs"] == 2 and len(result["open_job_list"]) == 2
    result, err = tool(s, "get_company", {"company_id": data.pending.id})
    assert err

    result, err = tool(s, "read_site_page", {"slug": "faq"})
    assert not err and result["url"] == "pages/content.html?slug=faq"
    assert tool(s, "read_site_page", {"slug": "dieu-khoan"})[1] is True
    assert tool(s, "read_site_page", {"slug": "../admin"})[1] is True
    assert tool(s, "delete_job", {"job_id": react.id})[1] is True


def test_last_round_forces_text_answer(client, data, ai):
    ai["responses"] = [tool_response(("search_jobs", {}))] * chat_service.MAX_TOOL_ROUNDS + [text_response("Đây là kết quả")]
    r = ask(client)
    assert r.status_code == 200 and r.json()["reply"] == "Đây là kết quả"
    assert [req["final"] for req in ai["requests"]] == [False] * chat_service.MAX_TOOL_ROUNDS + [True]


def test_refusal_empty_and_truncated_answers(client, ai):
    ai["responses"] = [SimpleNamespace(stop_reason="refusal", content=[])]
    assert ask(client).json()["reply"] == chat_service.REFUSAL_REPLY
    ai["responses"] = [SimpleNamespace(stop_reason="end_turn", content=[])]
    assert ask(client).status_code == 502
    ai["responses"] = [text_response("Câu trả lời dài", stop_reason="max_tokens")]
    assert ask(client).json()["reply"] == "Câu trả lời dài…"


def test_quota_per_guest_ip_and_per_user(client, ai, monkeypatch):
    ai["responses"] = [text_response("ok")]
    monkeypatch.setattr(chat_service, "GUEST_HOURLY_LIMIT", 2)
    monkeypatch.setattr(chat_service, "USER_HOURLY_LIMIT", 3)
    ip_a, ip_b = {"X-Forwarded-For": "203.0.113.1, 10.0.0.1"}, {"X-Forwarded-For": "203.0.113.2"}
    assert ask(client, headers=ip_a).status_code == 200
    assert ask(client, headers=ip_a).status_code == 200
    r = ask(client, headers=ip_a)
    assert r.status_code == 429 and "Đăng nhập để có thêm lượt" in r.json()["detail"]
    assert ask(client, headers=ip_b).status_code == 200

    user = make_user(client)
    for _ in range(3):
        assert ask(client, headers={**user, **ip_a}).status_code == 200
    r = ask(client, headers=user)
    assert r.status_code == 429 and "Đăng nhập" not in r.json()["detail"]

    monkeypatch.setattr(chat_service, "TOTAL_HOURLY_LIMIT", len(chat_service._all_calls))
    r = ask(client, headers={"X-Forwarded-For": "203.0.113.9"})
    assert r.status_code == 429 and "quá tải" in r.json()["detail"]


def test_sdk_request_and_error_mapping(client, monkeypatch):
    anthropic = pytest.importorskip("anthropic")
    import httpx2

    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "sk-test")
    chat_service._client.cache_clear()
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    outcomes = [
        text_response("Xin chào"),
        anthropic.RateLimitError("rate", response=httpx2.Response(429, request=request), body=None),
        anthropic.AuthenticationError("auth", response=httpx2.Response(401, request=request), body=None),
        anthropic.InternalServerError("boom", response=httpx2.Response(500, request=request), body=None),
        anthropic.APITimeoutError(request=request),
    ]
    expected = [200, 429, 503, 503, 504]
    sent = {}

    class FakeClient:
        def __init__(self, **kwargs):
            sent["client"] = kwargs
            self.messages = SimpleNamespace(create=self.create)

        def create(self, **kwargs):
            sent["request"] = kwargs
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

    monkeypatch.setattr(anthropic, "Anthropic", FakeClient)
    try:
        for status in expected:
            assert ask(client, "Chào").status_code == status
    finally:
        chat_service._client.cache_clear()
    assert sent["client"]["api_key"] == "sk-test"
    req = sent["request"]
    assert req["model"] == settings.AI_CHAT_MODEL == "claude-haiku-5-5"
    assert req["output_config"] == {"effort": "low"} and req["tool_choice"] == {"type": "auto"}
    assert {t["name"] for t in req["tools"]} == set(chat_service.TOOL_HANDLERS)
    assert "temperature" not in req and "fallbacks" not in req
