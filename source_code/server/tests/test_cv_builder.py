"""Trình tạo CV trực tuyến: lưu CV PDF kèm nội dung, mở lại, cập nhật (BR-15) và tạo nội dung bằng AI."""
import base64
import json
import os
from types import SimpleNamespace

import pytest

from src.config.settings import settings
from src.models import CV, Application, CandidateProfile
from src.services import cv_ai_service

BASE = "/api/v1/candidates/me"
PDF = b"%PDF-1.4\n" + b"x" * 100
PHOTO = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff\xe0" + b"0" * 64).decode()


@pytest.fixture(autouse=True)
def tmp_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture(autouse=True)
def reset_ai_quota():
    cv_ai_service._calls.clear()
    yield
    cv_ai_service._calls.clear()


def make_user(client, email="cand@example.com", role="CANDIDATE"):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "Abcd1234", "full_name": "Nguyen Van A", "role": role})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Abcd1234"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def cv_content(**overrides):
    data = {
        "template": "modern",
        "photo": PHOTO,
        "personal": {"full_name": "  Nguyễn Văn A ", "title": "Backend Developer", "email": "a@example.com"},
        "summary": "Lập trình viên Python.",
        "experience": [{"title": "Backend Developer", "subtitle": "Công ty X", "start": "01/2023", "end": "Hiện tại",
                        "description": "Xây dựng API\nTối ưu truy vấn"},
                       {"title": "", "subtitle": "", "start": "", "end": "", "description": ""}],
        "skills": ["Python", "", "SQL"],
    }
    data.update(overrides)
    return data


def save(client, headers, data, cv_id=None, name="CV - Nguyen Van A.pdf", content=PDF, mime="application/pdf"):
    files = {"file": (name, content, mime)}
    form = {"data": data if isinstance(data, str) else json.dumps(data)}
    if cv_id is None:
        return client.post(f"{BASE}/cvs/builder", headers=headers, files=files, data=form)
    return client.put(f"{BASE}/cvs/{cv_id}/builder", headers=headers, files=files, data=form)


def upload(client, headers):
    return client.post(f"{BASE}/cvs", headers=headers, files={"file": ("cv.pdf", PDF, "application/pdf")})


# ---------- Lưu và mở lại ----------

def test_create_and_reopen_builder_cv(client):
    h = make_user(client)
    r = save(client, h, cv_content())
    assert r.status_code == 201, r.text
    cv = r.json()
    assert cv["has_builder_data"] is True and cv["is_default"] is True
    assert cv["file_name"] == "CV - Nguyen Van A.pdf"
    upload(client, h)

    listing = client.get(f"{BASE}/cvs", headers=h).json()
    assert listing["total"] == 2
    assert {item["id"]: item["has_builder_data"] for item in listing["items"]}[cv["id"]] is True
    assert sorted(item["has_builder_data"] for item in listing["items"]) == [False, True]

    opened = client.get(f"{BASE}/cvs/{cv['id']}/builder", headers=h)
    assert opened.status_code == 200, opened.text
    data = opened.json()["data"]
    assert opened.json()["cv"]["id"] == cv["id"]
    assert data["template"] == "modern" and data["photo"] == PHOTO
    assert data["personal"]["full_name"] == "Nguyễn Văn A"
    assert len(data["experience"]) == 1  # bỏ mục để trống
    assert data["skills"] == ["Python", "SQL"]
    assert data["education"] == [] and data["summary"] == "Lập trình viên Python."

    download = client.get(f"{BASE}/cvs/{cv['id']}/download", headers=h)
    assert download.status_code == 200 and download.content == PDF


def test_builder_data_validation(client, tmp_upload_dir):
    h = make_user(client)
    cases = [
        (cv_content(personal={"full_name": " "}), "Hãy nhập họ và tên"),
        (cv_content(personal={"full_name": "A" * 151}), "Họ và tên tối đa 150 ký tự"),
        (cv_content(template="fancy"), None),
        (cv_content(photo="data:image/svg+xml;base64,PHN2Zz4="), "Ảnh CV phải là ảnh JPG, PNG hoặc WEBP"),
        (cv_content(photo="data:image/png;base64," + base64.b64encode(b"not a png").decode()), "Ảnh CV bị hỏng"),
        (cv_content(photo="data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff" + b"0" * 310_000).decode()),
         "Ảnh CV tối đa 300 KB"),
        (cv_content(skills=["kỹ năng"] * 41), "Kỹ năng tối đa 40 mục"),
        ("{not json", "Dữ liệu CV không hợp lệ"),
    ]
    for data, message in cases:
        r = save(client, h, data)
        assert r.status_code == 422, (data, r.text)
        if message:
            assert message in r.json()["detail"], r.text
    assert save(client, h, cv_content(), name="cv.docx", mime="application/octet-stream").status_code == 415
    assert save(client, h, cv_content(), content=b"MZ not a pdf").status_code == 415
    assert client.get(f"{BASE}/cvs", headers=h).json()["total"] == 0
    assert not os.path.isdir(tmp_upload_dir / "cvs") or os.listdir(tmp_upload_dir / "cvs") == []


# ---------- Cập nhật ----------

def test_update_replaces_unused_cv(client, tmp_upload_dir):
    h = make_user(client)
    first = save(client, h, cv_content()).json()
    other = upload(client, h).json()
    assert first["is_default"] is True and other["is_default"] is False

    r = save(client, h, cv_content(summary="Bản mới"), cv_id=first["id"], name="CV moi.pdf")
    assert r.status_code == 200, r.text
    updated = r.json()
    assert updated["id"] != first["id"] and updated["is_default"] is True and updated["file_name"] == "CV moi.pdf"

    listing = client.get(f"{BASE}/cvs", headers=h).json()
    assert sorted(item["id"] for item in listing["items"]) == sorted([updated["id"], other["id"]])
    assert len(os.listdir(tmp_upload_dir / "cvs")) == 2  # tệp của bản cũ đã xóa
    assert client.get(f"{BASE}/cvs/{updated['id']}/builder", headers=h).json()["data"]["summary"] == "Bản mới"
    assert client.get(f"{BASE}/cvs/{first['id']}/builder", headers=h).status_code == 404


def test_update_keeps_cv_attached_to_application(client, db_session, tmp_upload_dir):
    h = make_user(client)
    first = save(client, h, cv_content()).json()
    profile = db_session.query(CandidateProfile).one()
    db_session.add(Application(job_id=1, candidate_profile_id=profile.id, cv_id=first["id"]))
    db_session.commit()

    updated = save(client, h, cv_content(summary="Bản mới"), cv_id=first["id"]).json()
    assert updated["is_default"] is True
    assert [item["id"] for item in client.get(f"{BASE}/cvs", headers=h).json()["items"]] == [updated["id"]]
    db_session.expire_all()
    old = db_session.get(CV, first["id"])
    assert old.deleted_at is not None and old.is_default is False  # đơn đã nộp vẫn giữ CV cũ (BR-15)
    assert len(os.listdir(tmp_upload_dir / "cvs")) == 2


def test_update_rules_and_count_limit(client):
    h = make_user(client)
    builder_cv = save(client, h, cv_content()).json()
    uploaded = [upload(client, h).json() for _ in range(4)]
    assert save(client, h, cv_content()).status_code == 409  # đã đủ 5 CV
    assert save(client, h, cv_content(), cv_id=builder_cv["id"]).status_code == 200  # cập nhật không tính thêm

    r = save(client, h, cv_content(), cv_id=uploaded[0]["id"])
    assert r.status_code == 409 and "trình tạo CV" in r.json()["detail"]
    assert client.get(f"{BASE}/cvs/{uploaded[0]['id']}/builder", headers=h).status_code == 404
    assert client.get(f"{BASE}/cvs", headers=h).json()["total"] == 5

    h2 = make_user(client, email="b@example.com")
    upload(client, h2)  # ứng viên khác đã có hồ sơ riêng
    mine = client.get(f"{BASE}/cvs", headers=h).json()["items"]
    target = next(item for item in mine if item["has_builder_data"])
    assert client.get(f"{BASE}/cvs/{target['id']}/builder", headers=h2).status_code == 404
    assert save(client, h2, cv_content(), cv_id=target["id"]).status_code == 404


def test_builder_requires_candidate(client):
    assert save(client, {}, cv_content()).status_code == 401
    h = make_user(client, email="emp@example.com", role="EMPLOYER")
    assert save(client, h, cv_content()).status_code == 403
    assert client.post(f"{BASE}/cvs/builder/ai", headers=h, json={"text": "x" * 40}).status_code == 403


# ---------- Tạo nội dung bằng AI ----------

def fake_response(payload, stop_reason="end_turn", before=()):
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return SimpleNamespace(stop_reason=stop_reason,
                           content=[*before, SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)])


@pytest.fixture()
def ai(monkeypatch):
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "sk-test")
    state = {"prompts": [], "response": fake_response({"personal": {"full_name": "Trần Thị B"}})}

    def create(prompt):
        state["prompts"].append(prompt)
        return state["response"]
    monkeypatch.setattr(cv_ai_service, "_create_message", create)
    return state


INFO = "Tôi tên Trần Thị B, tốt nghiệp ĐH Kinh tế năm 2023, làm marketing 2 năm ở công ty Y."


def test_ai_disabled_without_key(client, monkeypatch):
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
    h = make_user(client)
    r = client.post(f"{BASE}/cvs/builder/ai", headers=h, json={"text": INFO})
    assert r.status_code == 503 and "ANTHROPIC_API_KEY" in r.json()["detail"]


def test_ai_generates_clipped_content(client, ai):
    ai["response"] = fake_response({
        "personal": {"full_name": "Trần Thị B", "title": "Marketing Executive", "unknown": "x"},
        "summary": "S" * 5000,
        "experience": [{"title": "Marketing", "subtitle": "Công ty Y", "start": "2023", "end": "Hiện tại",
                        "description": "Lập kế hoạch\nChạy quảng cáo"},
                       {"title": "", "subtitle": "", "start": "", "end": "", "description": ""}],
        "education": "không phải danh sách",
        "skills": ["SEO", "", 7] + [f"Kỹ năng {i}" for i in range(50)],
        "certificates": ["C" * 300],
    })
    h = make_user(client)
    r = client.post(f"{BASE}/cvs/builder/ai", headers=h, json={"text": INFO, "target": " Marketing "})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["personal"]["full_name"] == "Trần Thị B" and data["personal"]["title"] == "Marketing Executive"
    assert "unknown" not in data["personal"] and data["personal"]["phone"] == ""
    assert len(data["summary"]) == 3000
    assert len(data["experience"]) == 1 and data["experience"][0]["subtitle"] == "Công ty Y"
    assert data["education"] == [] and data["projects"] == []
    assert data["skills"][0] == "SEO" and len(data["skills"]) == 40
    assert data["certificates"] == ["C" * 200]
    assert INFO in ai["prompts"][0] and "Vị trí muốn ứng tuyển: Marketing" in ai["prompts"][0]


def test_ai_reads_answer_after_fallback(client, ai):
    declined = SimpleNamespace(type="text", text='{"personal": {"full_name": "dở dang')
    switch = SimpleNamespace(type="fallback")
    ai["response"] = fake_response({"personal": {"full_name": "Trần Thị B"}}, before=(declined, switch))
    h = make_user(client)
    r = client.post(f"{BASE}/cvs/builder/ai", headers=h, json={"text": INFO})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["personal"]["full_name"] == "Trần Thị B"


def test_ai_errors_and_quota(client, ai):
    h = make_user(client)
    assert client.post(f"{BASE}/cvs/builder/ai", headers=h, json={"text": "ngắn quá"}).status_code == 422
    assert client.post(f"{BASE}/cvs/builder/ai", headers=h, json={"text": "x" * 8001}).status_code == 422

    ai["response"] = fake_response("", stop_reason="refusal")
    assert client.post(f"{BASE}/cvs/builder/ai", headers=h, json={"text": INFO}).status_code == 422
    ai["response"] = fake_response("{bad json")
    assert client.post(f"{BASE}/cvs/builder/ai", headers=h, json={"text": INFO}).status_code == 502

    ai["response"] = fake_response({"personal": {"full_name": "B"}})
    used = len(ai["prompts"])
    for _ in range(cv_ai_service.HOURLY_LIMIT - used):
        assert client.post(f"{BASE}/cvs/builder/ai", headers=h, json={"text": INFO}).status_code == 200
    r = client.post(f"{BASE}/cvs/builder/ai", headers=h, json={"text": INFO})
    assert r.status_code == 429 and "Mỗi giờ" in r.json()["detail"]
    other = make_user(client, email="other@example.com")
    assert client.post(f"{BASE}/cvs/builder/ai", headers=other, json={"text": INFO}).status_code == 200


def test_ai_maps_sdk_errors(client, monkeypatch):
    anthropic = pytest.importorskip("anthropic")
    import httpx2

    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "sk-test")
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    errors = [
        (anthropic.RateLimitError("rate", response=httpx2.Response(429, request=request), body=None), 429),
        (anthropic.AuthenticationError("auth", response=httpx2.Response(401, request=request), body=None), 503),
        (anthropic.InternalServerError("boom", response=httpx2.Response(500, request=request), body=None), 503),
        (anthropic.APITimeoutError(request=request), 504),
    ]
    sent = {}

    class FakeClient:
        def __init__(self, **kwargs):
            sent["client"] = kwargs
            self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

        def create(self, **kwargs):
            sent["request"] = kwargs
            raise errors[0][0]

    monkeypatch.setattr(anthropic, "Anthropic", FakeClient)
    h = make_user(client)
    while errors:
        r = client.post(f"{BASE}/cvs/builder/ai", headers=h, json={"text": INFO})
        assert r.status_code == errors[0][1], r.text
        errors.pop(0)
    assert sent["client"]["api_key"] == "sk-test"
    assert sent["request"]["model"] == settings.AI_CV_MODEL
    assert sent["request"]["output_config"]["format"]["type"] == "json_schema"
    assert sent["request"]["fallbacks"] == "default"
