import os

import pytest

from src.config.settings import settings
from src.models import CV, Application, CandidateProfile, Province, SystemSetting

PDF = b"%PDF-1.4\n" + b"x" * 100
DOCX = b"PK\x03\x04" + b"x" * 100
DOC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"x" * 100

BASE = "/api/v1/candidates/me"


@pytest.fixture(autouse=True)
def tmp_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


def make_user(client, email="cand@example.com", role="CANDIDATE"):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "Abcd1234", "full_name": "Nguyen Van A", "role": role})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Abcd1234"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def upload(client, h, name="cv.pdf", content=PDF, mime="application/pdf"):
    return client.post(f"{BASE}/cvs", headers=h, files={"file": (name, content, mime)})


# ---------- Hồ sơ ----------

def test_profile_crud(client, db_session):
    h = make_user(client)
    assert client.get(f"{BASE}/profile", headers=h).status_code == 404

    province = Province(name="Hà Nội", code="HN")
    db_session.add(province)
    db_session.commit()

    r = client.post(f"{BASE}/profile", headers=h, json={
        "date_of_birth": "2000-01-15", "gender": "MALE", "province_id": province.id,
        "headline": "  Backend Developer ", "summary": "Xin chào"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["full_name"] == "Nguyen Van A"  # giữ từ lúc đăng ký
    assert body["headline"] == "Backend Developer"
    assert body["visibility"] == "PUBLIC"
    assert client.post(f"{BASE}/profile", headers=h, json={}).status_code == 409

    r = client.patch(f"{BASE}/profile", headers=h, json={
        "full_name": "Tran Thi B", "phone": "0912345678", "visibility": "PRIVATE", "summary": None})
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["full_name"], body["phone"], body["visibility"]) == ("Tran Thi B", "0912345678", "PRIVATE")
    assert body["summary"] is None and body["headline"] == "Backend Developer"

    assert client.get(f"{BASE}/profile", headers=h).json()["full_name"] == "Tran Thi B"
    assert client.delete(f"{BASE}/profile", headers=h).status_code == 204
    assert client.get(f"{BASE}/profile", headers=h).status_code == 404


def test_profile_validation(client):
    h = make_user(client)
    assert client.post(f"{BASE}/profile", headers=h, json={"gender": "X"}).status_code == 422
    assert client.post(f"{BASE}/profile", headers=h, json={"date_of_birth": "2999-01-01"}).status_code == 422
    assert client.post(f"{BASE}/profile", headers=h, json={"province_id": 999}).status_code == 422
    assert client.post(f"{BASE}/profile", headers=h, json={"headline": "a" * 151}).status_code == 422
    assert client.post(f"{BASE}/profile", headers=h, json={}).status_code == 201
    assert client.patch(f"{BASE}/profile", headers=h, json={"full_name": None}).status_code == 422
    assert client.patch(f"{BASE}/profile", headers=h, json={"visibility": None}).status_code == 422
    assert client.patch(f"{BASE}/profile", headers=h, json={"phone": "abc"}).status_code == 422


def test_profile_requires_candidate_role(client):
    assert client.get(f"{BASE}/profile").status_code == 401
    h = make_user(client, email="emp@example.com", role="EMPLOYER")
    assert client.get(f"{BASE}/profile", headers=h).status_code == 403
    assert upload(client, h).status_code == 403


def test_delete_profile_blocked_when_has_applications(client, db_session):
    h = make_user(client)
    cv_id = upload(client, h).json()["id"]
    profile = db_session.query(CandidateProfile).one()
    _fake_application(db_session, profile.id, cv_id)
    assert client.delete(f"{BASE}/profile", headers=h).status_code == 409


# ---------- CV ----------

def test_upload_list_download_delete(client, tmp_upload_dir):
    h = make_user(client)
    assert client.get(f"{BASE}/cvs", headers=h).json()["total"] == 0

    r = upload(client, h, name="CV Nguyen Van A.pdf")
    assert r.status_code == 201, r.text
    first = r.json()
    assert first["is_default"] is True  # CV đầu tiên tự là mặc định (tự tạo hồ sơ)
    assert first["file_size"] == len(PDF)
    assert "file_url" not in first  # không lộ đường dẫn lưu trữ

    second = upload(client, h, name="cv.docx", content=DOCX).json()
    third = upload(client, h, name="cv.doc", content=DOC).json()
    assert second["is_default"] is False and third["is_default"] is False

    listing = client.get(f"{BASE}/cvs", headers=h).json()
    assert listing["total"] == 3 and listing["max_count"] == 5 and listing["max_size_mb"] == 5
    assert listing["items"][0]["id"] == first["id"]  # mặc định đứng đầu

    d = client.get(f"{BASE}/cvs/{first['id']}/download", headers=h)
    assert d.status_code == 200 and d.content == PDF
    assert d.headers["content-type"] == "application/pdf"

    assert len(os.listdir(tmp_upload_dir / "cvs")) == 3
    assert client.delete(f"{BASE}/cvs/{first['id']}", headers=h).status_code == 204
    assert len(os.listdir(tmp_upload_dir / "cvs")) == 2
    listing = client.get(f"{BASE}/cvs", headers=h).json()
    assert listing["total"] == 2
    assert [c["id"] for c in listing["items"] if c["is_default"]] == [third["id"]]  # mới nhất được chuyển làm mặc định
    assert client.delete(f"{BASE}/cvs/{first['id']}", headers=h).status_code == 404


def test_set_default(client):
    h = make_user(client)
    a = upload(client, h).json()
    b = upload(client, h).json()
    r = client.patch(f"{BASE}/cvs/{b['id']}/default", headers=h)
    assert r.status_code == 200 and r.json()["is_default"] is True
    defaults = [c["id"] for c in client.get(f"{BASE}/cvs", headers=h).json()["items"] if c["is_default"]]
    assert defaults == [b["id"]]
    assert a["id"] != b["id"]


def test_upload_rejects_bad_extension_and_spoofed_content(client, tmp_upload_dir):
    h = make_user(client)
    assert upload(client, h, name="cv.exe", content=b"MZ...").status_code == 415
    assert upload(client, h, name="cv", content=PDF).status_code == 415
    assert upload(client, h, name="cv.pdf", content=b"MZ not a pdf").status_code == 415
    assert upload(client, h, name="cv.docx", content=PDF).status_code == 415
    assert upload(client, h, name="cv.pdf", content=b"").status_code == 422
    assert os.listdir(tmp_upload_dir / "cvs") == []  # không để lại tệp rác


def test_upload_size_limit(client, db_session, tmp_upload_dir):
    h = make_user(client)
    too_big = b"%PDF-" + b"x" * (5 * 1024 * 1024)
    assert upload(client, h, content=too_big).status_code == 413
    assert os.listdir(tmp_upload_dir / "cvs") == []

    db_session.add(SystemSetting(setting_key="cv_max_size_mb", setting_value="1"))
    db_session.commit()
    assert upload(client, h, content=b"%PDF-" + b"x" * (1024 * 1024)).status_code == 413
    assert upload(client, h, content=b"%PDF-" + b"x" * 1000).status_code == 201


def test_upload_count_limit(client):
    h = make_user(client)
    for _ in range(5):
        assert upload(client, h).status_code == 201
    assert upload(client, h).status_code == 409
    cv_id = client.get(f"{BASE}/cvs", headers=h).json()["items"][-1]["id"]
    client.delete(f"{BASE}/cvs/{cv_id}", headers=h)
    assert upload(client, h).status_code == 201


def test_cannot_touch_other_candidates_cv(client):
    h1 = make_user(client, email="a@example.com")
    h2 = make_user(client, email="b@example.com")
    cv_id = upload(client, h1).json()["id"]
    upload(client, h2)
    assert client.get(f"{BASE}/cvs/{cv_id}/download", headers=h2).status_code == 404
    assert client.patch(f"{BASE}/cvs/{cv_id}/default", headers=h2).status_code == 404
    assert client.delete(f"{BASE}/cvs/{cv_id}", headers=h2).status_code == 404
    assert client.get(f"{BASE}/cvs", headers=h1).json()["total"] == 1


def test_delete_cv_used_in_application_is_soft(client, db_session, tmp_upload_dir):
    h = make_user(client)
    cv_id = upload(client, h).json()["id"]
    profile = db_session.query(CandidateProfile).one()
    _fake_application(db_session, profile.id, cv_id)

    assert client.delete(f"{BASE}/cvs/{cv_id}", headers=h).status_code == 204
    assert client.get(f"{BASE}/cvs", headers=h).json()["total"] == 0
    db_session.expire_all()
    cv = db_session.get(CV, cv_id)
    assert cv is not None and cv.deleted_at is not None  # vẫn giữ cho đơn ứng tuyển
    assert len(os.listdir(tmp_upload_dir / "cvs")) == 1


def _fake_application(db_session, profile_id, cv_id):
    """Chèn đơn ứng tuyển tối thiểu (SQLite test không bật kiểm tra khóa ngoại)."""
    db_session.add(Application(job_id=1, candidate_profile_id=profile_id, cv_id=cv_id))
    db_session.commit()
