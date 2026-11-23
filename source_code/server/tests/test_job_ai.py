"""Xác minh doanh nghiệp (tick vàng) và AI theo tin tuyển dụng: chấm điểm CV, tối ưu CV, viết tin tuyển dụng."""
import base64
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.config.settings import settings
from src.models import AuditLog, Company, CompanyMember, Industry, Job, Province, Role, User
from src.services import job_ai_service
from src.services.public_service import today
from src.utils.security import hash_password

CAND = "/api/v1/candidates/me"
ADM = "/api/v1/admin/companies"
PDF = b"%PDF-1.4\n" + b"x" * 100
PHOTO = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff\xe0" + b"0" * 64).decode()


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    job_ai_service._calls.clear()
    yield
    job_ai_service._calls.clear()


def login(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Abcd1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def register(client, email, role):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "Abcd1234", "full_name": "Nguyen Van A", "role": role})
    return login(client, email)


def make_user(db, email, role):
    db.add(User(email=email, password_hash=hash_password("Abcd1234"), full_name=role.title(),
                role_id=db.query(Role.id).filter(Role.name == role).scalar()))
    db.commit()
    return db.query(User).filter(User.email == email).one()


@pytest.fixture()
def world(client, db_session):
    s = db_session
    owner = make_user(s, "hr@example.com", "EMPLOYER")
    it = Industry(name="Công nghệ thông tin", slug="cntt")
    hcm = Province(name="TP. Hồ Chí Minh", code="HCM")
    acme = Company(name="Acme Việt Nam", slug="acme", status="APPROVED", size="51-200", description="Công ty phần mềm.")
    pending = Company(name="Pending Co", slug="pending", status="PENDING")
    s.add_all([it, hcm, acme, pending])
    s.flush()
    acme.industry_id = it.id
    s.add(CompanyMember(company_id=acme.id, user_id=owner.id, member_role="OWNER"))

    def job(title, company, **kw):
        values = dict(company_id=company.id, created_by=owner.id, title=title, status="APPROVED",
                      deadline=today() + timedelta(days=10), published_at=datetime.now(timezone.utc).replace(tzinfo=None),
                      industry_id=it.id, province_id=hcm.id, salary_min=15_000_000, salary_max=25_000_000,
                      employment_type="FULL_TIME", experience_level="FROM_1_TO_3",
                      description="Phát triển giao diện React.", requirements="1 năm React, TypeScript.",
                      benefits="Thưởng tháng 13.")
        values.update(kw)
        row = Job(**values)
        s.add(row)
        s.flush()
        return row

    react = job("Frontend React Developer", acme)
    draft = job("Hidden Draft", acme, status="DRAFT")
    s.commit()
    return SimpleNamespace(acme=acme, pending=pending, react=react, draft=draft, industry=it, province=hcm,
                           employer=login(client, "hr@example.com"))


def builder_cv(client, headers, **overrides):
    data = {"template": "modern", "photo": PHOTO,
            "personal": {"full_name": "Nguyễn Văn A", "title": "Backend Developer", "email": "a@example.com",
                         "phone": "0901234567"},
            "summary": "Lập trình viên web.",
            "experience": [{"title": "Developer", "subtitle": "Công ty X", "start": "2023", "end": "Hiện tại",
                            "description": "Xây dựng giao diện React"}],
            "skills": ["React", "SQL"]}
    data.update(overrides)
    r = client.post(f"{CAND}/cvs/builder", headers=headers, data={"data": json.dumps(data)},
                    files={"file": ("CV - A.pdf", PDF, "application/pdf")})
    assert r.status_code == 201, r.text
    return r.json()


def upload_cv(client, headers, name="cv.pdf", content=PDF, mime="application/pdf"):
    r = client.post(f"{CAND}/cvs", headers=headers, files={"file": (name, content, mime)})
    assert r.status_code == 201, r.text
    return r.json()


def fake_response(payload, stop_reason="end_turn"):
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="thinking", thinking=""),
                                                             SimpleNamespace(type="text", text=text)])


@pytest.fixture()
def ai(monkeypatch):
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "sk-test")
    state = {"calls": [], "response": None}

    def create(model, system, content, schema, **options):
        state["calls"].append(dict(model=model, system=system, content=content, schema=schema, **options))
        return state["response"]
    monkeypatch.setattr(job_ai_service, "_create_message", create)
    return state


def prompt_text(call):
    return "\n".join(block.get("text", "") for block in call["content"])


# ---------- Xác minh doanh nghiệp ----------

def test_admin_verifies_approved_company(client, db_session, world):
    make_user(db_session, "admin@example.com", "ADMIN")
    adm = login(client, "admin@example.com")
    url = f"{ADM}/{world.acme.id}/verification"

    assert client.get(f"/api/v1/companies/{world.acme.id}").json()["is_verified"] is False
    assert client.put(url, headers=world.employer, json={"verified": True}).status_code == 403
    assert client.put(f"{ADM}/{world.pending.id}/verification", headers=adm, json={"verified": True}).status_code == 409

    r = client.put(url, headers=adm, json={"verified": True})
    assert r.status_code == 200, r.text
    assert r.json()["is_verified"] is True and r.json()["verified_at"]
    assert client.put(url, headers=adm, json={"verified": True}).status_code == 200  # gọi lại không ghi log trùng

    assert client.get(f"/api/v1/companies/{world.acme.id}").json()["is_verified"] is True
    listed = client.get("/api/v1/companies").json()["items"]
    assert {c["name"]: c["is_verified"] for c in listed}["Acme Việt Nam"] is True
    assert client.get(f"/api/v1/jobs/{world.react.id}").json()["company_verified"] is True
    assert client.get("/api/v1/jobs").json()["items"][0]["company_verified"] is True
    assert client.get("/api/v1/employer/company", headers=world.employer).json()["is_verified"] is True
    assert client.get(ADM, headers=adm).json()["items"][0]["is_verified"] in (True, False)

    r = client.put(url, headers=adm, json={"verified": False})
    assert r.json()["is_verified"] is False and r.json()["verified_at"] is None
    assert client.get(f"/api/v1/jobs/{world.react.id}").json()["company_verified"] is False
    actions = [a for (a,) in db_session.query(AuditLog.action).filter(AuditLog.entity_type == "COMPANY")]
    assert actions == ["COMPANY_VERIFY", "COMPANY_UNVERIFY"]


# ---------- Chấm điểm phù hợp ----------

MATCH = {"score": 182, "verdict": "Bạn khá phù hợp.", "matched_skills": ["React", "", "SQL"],
         "missing_skills": ["TypeScript"], "strengths": ["Có kinh nghiệm React"] + ["x"] * 20,
         "gaps": ["G" * 500], "tips": ["Bổ sung dự án TypeScript"]}


def test_match_with_builder_and_pdf_cv(client, world, ai):
    h = register(client, "cand@example.com", "CANDIDATE")
    online = builder_cv(client, h)
    ai["response"] = fake_response(MATCH)

    r = client.post(f"{CAND}/job-match", headers=h, json={"job_id": world.react.id, "cv_id": online["id"]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["score"] == 100 and body["cv_name"] == "CV - A.pdf" and body["job_id"] == world.react.id
    assert body["matched_skills"] == ["React", "SQL"]
    assert len(body["strengths"]) == 8 and len(body["gaps"][0]) == 300
    call = ai["calls"][0]
    assert call["model"] == settings.AI_JOB_MODEL and call.get("fallback", False) is False
    text = prompt_text(call)
    assert "Frontend React Developer" in text and "Acme Việt Nam" in text and "1 năm React" in text
    assert '"Xây dựng giao diện React"' in text and PHOTO not in text  # gửi nội dung CV, không gửi ảnh
    assert call["schema"]["properties"]["score"]["type"] == "integer"

    uploaded = upload_cv(client, h)
    ai["response"] = fake_response({**MATCH, "score": "61.6"})
    r = client.post(f"{CAND}/job-match", headers=h, json={"job_id": world.react.id, "cv_id": uploaded["id"]})
    assert r.status_code == 200, r.text
    assert r.json()["score"] == 62
    document = ai["calls"][1]["content"][0]
    assert document["type"] == "document" and base64.b64decode(document["source"]["data"]) == PDF


def test_match_rejects_bad_inputs(client, monkeypatch, world, ai):
    h = register(client, "cand@example.com", "CANDIDATE")
    online = builder_cv(client, h)
    other = register(client, "other@example.com", "CANDIDATE")
    docx = upload_cv(client, other, "cv.doc", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"0" * 64, "application/msword")
    ai["response"] = fake_response(MATCH)

    def post(headers, job_id, cv_id):
        return client.post(f"{CAND}/job-match", headers=headers, json={"job_id": job_id, "cv_id": cv_id})

    assert post(h, world.draft.id, online["id"]).status_code == 404          # tin không công khai
    assert post(other, world.react.id, online["id"]).status_code == 404      # CV của người khác
    r = post(other, world.react.id, docx["id"])
    assert r.status_code == 422 and "PDF" in r.json()["detail"]
    assert post(world.employer, world.react.id, online["id"]).status_code == 403
    assert client.post(f"{CAND}/job-match", json={"job_id": world.react.id, "cv_id": online["id"]}).status_code in (401, 403)
    assert ai["calls"] == []  # lỗi đầu vào không gọi AI, không tốn lượt

    ai["response"] = fake_response({**MATCH, "score": "cao"})
    assert post(h, world.react.id, online["id"]).status_code == 502
    ai["response"] = fake_response("", stop_reason="refusal")
    assert post(h, world.react.id, online["id"]).status_code == 422
    ai["response"] = fake_response("{bad")
    assert post(h, world.react.id, online["id"]).status_code == 502

    ai["response"] = fake_response(MATCH)
    for _ in range(job_ai_service.MATCH_HOURLY_LIMIT - len(ai["calls"])):
        assert post(h, world.react.id, online["id"]).status_code == 200
    r = post(h, world.react.id, online["id"])
    assert r.status_code == 429 and "Mỗi giờ" in r.json()["detail"]

    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
    r = post(other, world.react.id, docx["id"])
    assert r.status_code == 503 and "ANTHROPIC_API_KEY" in r.json()["detail"]


# ---------- Tối ưu CV theo tin ----------

def tailored(**personal):
    return {"cv": {"personal": {"full_name": "Tên Khác", "title": "Frontend React Developer", "phone": "999", **personal},
                   "summary": "Lập trình viên React với kinh nghiệm xây dựng giao diện.",
                   "experience": [{"title": "Developer", "subtitle": "Công ty X", "start": "2023", "end": "Hiện tại",
                                   "description": "Xây dựng giao diện React"}],
                   "skills": ["React", "SQL"]},
            "changes": ["Viết lại phần giới thiệu", "", "Tin cần TypeScript: bổ sung nếu bạn có"]}


def test_tailor_keeps_personal_info_and_photo(client, world, ai):
    h = register(client, "cand@example.com", "CANDIDATE")
    online = builder_cv(client, h)
    ai["response"] = fake_response(tailored())

    r = client.post(f"{CAND}/cvs/builder/tailor", headers=h, json={"job_id": world.react.id, "cv_id": online["id"]})
    assert r.status_code == 200, r.text
    body = r.json()
    personal = body["data"]["personal"]
    assert personal["full_name"] == "Nguyễn Văn A" and personal["phone"] == "0901234567"  # giữ nguyên CV gốc
    assert personal["title"] == "Frontend React Developer"                              # chỉ đổi vị trí
    assert body["template"] == "modern" and body["photo"] == PHOTO and body["source_cv_id"] == online["id"]
    assert body["job_title"] == "Frontend React Developer" and body["company_name"] == "Acme Việt Nam"
    assert body["changes"] == ["Viết lại phần giới thiệu", "Tin cần TypeScript: bổ sung nếu bạn có"]
    call = ai["calls"][0]
    assert call["model"] == settings.AI_CV_MODEL and call["fallback"] is True
    assert "$defs" in call["schema"] and "cv" in call["schema"]["properties"]

    uploaded = upload_cv(client, h)
    ai["response"] = fake_response(tailored(full_name="Trần B"))
    body = client.post(f"{CAND}/cvs/builder/tailor", headers=h, json={"job_id": world.react.id, "cv_id": uploaded["id"]}).json()
    assert body["data"]["personal"]["full_name"] == "Trần B"  # CV PDF: thông tin AI đọc từ tệp
    assert body["template"] == "elegant" and body["photo"] is None

    ai["response"] = fake_response({"cv": {}, "changes": []})
    r = client.post(f"{CAND}/cvs/builder/tailor", headers=h, json={"job_id": world.react.id, "cv_id": online["id"]})
    assert r.status_code == 502


# ---------- Viết tin tuyển dụng ----------

DRAFT_URL = "/api/v1/employer/jobs/ai-draft"


def test_employer_drafts_job_with_ai(client, world, ai):
    ai["response"] = fake_response({"title": "  Lập trình viên   React ",
                                    "description": "- Phát triển giao diện\n\n• Viết kiểm thử\n",
                                    "requirements": "1. Thành thạo React\nƯu tiên biết TypeScript",
                                    "benefits": ""})
    body = {"title": "Frontend dev", "notes": "Team 5 người, làm sản phẩm SaaS", "industry_id": world.industry.id,
            "province_id": world.province.id, "employment_type": "FULL_TIME", "experience_level": "FROM_1_TO_3",
            "salary_min": 15_000_000, "salary_max": 25_000_000, "positions": 2}
    r = client.post(DRAFT_URL, headers=world.employer, json=body)
    assert r.status_code == 200, r.text
    result = r.json()
    assert result["title"] == "Lập trình viên React"
    assert result["description"] == "Phát triển giao diện\nViết kiểm thử"
    assert result["requirements"] == "1. Thành thạo React\nƯu tiên biết TypeScript" and result["benefits"] == ""
    text = prompt_text(ai["calls"][0])
    for expected in ("Frontend dev", "Team 5 người", "Công nghệ thông tin", "TP. Hồ Chí Minh", "Toàn thời gian",
                     "15 – 25 triệu", "2 người", "Acme Việt Nam", "Công ty phần mềm."):
        assert expected in text, expected
    assert ai["calls"][0]["model"] == settings.AI_JOB_MODEL

    ai["response"] = fake_response({"title": "IT", "description": "Viết code", "requirements": "React", "benefits": ""})
    assert client.post(DRAFT_URL, headers=world.employer, json={"title": "Frontend dev"}).json()["title"] == "Frontend dev"
    ai["response"] = fake_response({"title": "Frontend", "description": "", "requirements": "", "benefits": ""})
    assert client.post(DRAFT_URL, headers=world.employer, json={"title": "Frontend dev"}).status_code == 502

    assert client.post(DRAFT_URL, headers=world.employer, json={"title": "IT"}).status_code == 422
    assert client.post(DRAFT_URL, headers=world.employer, json={"title": "Frontend dev", "notes": "x" * 3001}).status_code == 422
    cand = register(client, "cand@example.com", "CANDIDATE")
    assert client.post(DRAFT_URL, headers=cand, json={"title": "Frontend dev"}).status_code == 403
    newcomer = register(client, "new@example.com", "EMPLOYER")
    assert client.post(DRAFT_URL, headers=newcomer, json={"title": "Frontend dev"}).status_code == 403  # chưa có công ty duyệt


def test_sdk_request_shape(client, monkeypatch, world):
    anthropic = pytest.importorskip("anthropic")
    import httpx2

    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "sk-test")
    job_ai_service._client.cache_clear()
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    sent = []

    class FakeClient:
        def __init__(self, **kwargs):
            self.messages = SimpleNamespace(create=lambda **kw: sent.append(("plain", kw)) or fake_response(
                {"title": "Lập trình viên React", "description": "Viết code", "requirements": "React", "benefits": ""}))
            self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.fail))

        def fail(self, **kw):
            sent.append(("beta", kw))
            raise anthropic.RateLimitError("rate", response=httpx2.Response(429, request=request), body=None)

    monkeypatch.setattr(anthropic, "Anthropic", FakeClient)
    try:
        r = client.post(DRAFT_URL, headers=world.employer, json={"title": "Frontend dev"})
        assert r.status_code == 200, r.text
        kind, params = sent[0]
        assert kind == "plain" and params["model"] == settings.AI_JOB_MODEL and "fallbacks" not in params
        assert params["output_config"]["format"]["type"] == "json_schema" and "temperature" not in params

        h = register(client, "cand@example.com", "CANDIDATE")
        online = builder_cv(client, h)
        r = client.post(f"{CAND}/cvs/builder/tailor", headers=h, json={"job_id": world.react.id, "cv_id": online["id"]})
        assert r.status_code == 429
        kind, params = sent[1]
        assert kind == "beta" and params["fallbacks"] == "default" and params["model"] == settings.AI_CV_MODEL
    finally:
        job_ai_service._client.cache_clear()
