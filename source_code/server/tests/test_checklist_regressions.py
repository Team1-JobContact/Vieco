from io import BytesIO
from pathlib import Path
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from jose import jwt

from src.config.settings import SERVER_DIR, Settings, settings
from src.models import AuditLog, Industry, Role, StaticPage, User
from src.seeds.run import seed_admin
from tests.test_candidate import make_user, upload
from tests.test_design_api import actor, recruitment
from tests.test_workflows import upload_image


@pytest.fixture(autouse=True)
def isolated_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


def test_admin_accounts_filters_lock_unlock_and_audit(client, db_session):
    admin_user, admin = actor(db_session, "ADMIN", "admin-check@example.com")
    candidate, headers = actor(db_session, "CANDIDATE", "person-check@example.com")
    assert client.get("/api/v1/admin/users").status_code == 401
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 403
    result = client.get("/api/v1/admin/users?q=person-check&role=CANDIDATE", headers=admin).json()
    assert result["total"] == 1
    assert "password_hash" not in result["items"][0]
    assert client.get("/api/v1/admin/users?page_size=101", headers=admin).status_code == 422
    path = f"/api/v1/admin/users/{candidate.id}/status"
    assert client.patch(path, headers=headers, json={"status": "LOCKED"}).status_code == 403
    assert client.patch(path, headers=admin, json={"status": "LOCKED", "role": "ADMIN"}).status_code == 422
    assert client.patch(path, headers=admin, json={"status": "LOCKED"}).status_code == 200
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": candidate.email, "password": "Abcd1234"}).status_code == 403
    assert client.get("/api/v1/admin/users?status=LOCKED", headers=admin).json()["total"] == 1
    assert client.patch(path, headers=admin, json={"status": "ACTIVE"}).status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": candidate.email, "password": "Abcd1234"}).status_code == 200
    logs = client.get("/api/v1/admin/audit-logs", headers=admin).json()
    assert logs["total"] == 2 and logs["items"][0]["actor_name"] == admin_user.full_name
    assert db_session.query(AuditLog).filter(AuditLog.action == "USER_STATUS").count() == 2
    assert client.get("/api/v1/admin/users/99999", headers=admin).status_code == 404


def test_admin_categories_hide_preserve_slug_and_reject_duplicates(client, db_session):
    _, admin = actor(db_session, "ADMIN", "catalog-check@example.com")
    body = {"type": "industries", "name": "Công nghệ thông tin"}
    created = client.post("/api/v1/admin/categories", headers=admin, json=body).json()
    db_session.add(Industry(name="Khác", slug="khac"))
    db_session.commit()
    path = f"/api/v1/admin/categories/industries/{created['id']}"
    assert client.patch(path, headers=admin, json={**body, "name": "Khác", "is_active": False}).status_code == 409
    response = client.patch(path, headers=admin, json={**body, "name": "CNTT", "is_active": False})
    assert response.status_code == 200
    assert response.json()["slug"] == created["slug"]
    assert all(row["id"] != created["id"] for row in client.get("/api/v1/categories").json()["industries"])
    assert any(row["id"] == created["id"] for row in client.get("/api/v1/admin/categories", headers=admin).json()["industries"])
    assert client.patch(path, headers=admin, json={"type": "skills", "name": "Wrong"}).status_code == 422
    assert client.patch(path, headers=admin, json={**body, "is_active": True}).status_code == 200


def test_static_pages_publish_update_and_permissions(client, db_session):
    _, admin = actor(db_session, "ADMIN", "pages-check@example.com")
    _, candidate = actor(db_session, "CANDIDATE", "pages-user@example.com")
    page = StaticPage(slug="gioi-thieu", title="Giới thiệu", content="Nội dung cũ", is_published=False)
    db_session.add(page)
    db_session.commit()
    path = f"/api/v1/admin/pages/{page.id}"
    data = {"title": "Vieco", "content": "Nội dung mới", "is_published": True}
    assert client.get("/api/v1/pages/gioi-thieu").status_code == 404
    assert client.get("/api/v1/admin/pages", headers=candidate).status_code == 403
    assert client.patch(path, headers=candidate, json=data).status_code == 403
    assert client.patch(path, headers=admin, json={**data, "title": "   "}).status_code == 422
    assert client.patch(path, headers=admin, json=data).status_code == 200
    assert client.get("/api/v1/pages/gioi-thieu").json()["content"] == "Nội dung mới"
    assert client.patch(path, headers=admin, json={**data, "is_published": False}).status_code == 200
    assert client.get("/api/v1/pages/gioi-thieu").status_code == 404


def test_admin_upload_settings_validate_and_apply(client, db_session):
    _, admin = actor(db_session, "ADMIN", "settings-check@example.com")
    candidate = make_user(client)
    path = "/api/v1/admin/upload-settings/cv_max_count"
    assert len(client.get("/api/v1/admin/upload-settings", headers=admin).json()) == 4
    assert client.patch(path, headers=candidate, json={"value": "1"}).status_code == 403
    for value in ("0", "-1", "1.5", "abc"):
        assert client.patch(path, headers=admin, json={"value": value}).status_code == 422
    assert client.patch(path, headers=admin, json={"value": "1"}).status_code == 200
    assert upload(client, candidate).status_code == 201
    assert upload(client, candidate).status_code == 409
    assert client.patch("/api/v1/admin/upload-settings/cv_allowed_extensions", headers=admin, json={"value": "pdf,exe"}).status_code == 422
    assert client.patch("/api/v1/admin/upload-settings/cv_allowed_extensions", headers=admin, json={"value": ".PDF"}).json()["value"] == "pdf"


@pytest.mark.parametrize("claims", [
    {"sub": "bad", "iat": 1, "exp": 4102444800},
    {"sub": "1", "exp": 4102444800},
    {"sub": "1", "iat": "bad", "exp": 4102444800},
    {"sub": "1", "iat": 1},
])
def test_malformed_signed_claims_return_401(client, claims):
    token = jwt.encode({"jti": "test-checklist", **claims}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_docx_rejects_fake_zip_and_cleans_files(client, isolated_uploads):
    candidate = make_user(client)
    assert upload(client, candidate, name="fake.docx", content=b"PK\x03\x04fake").status_code == 415
    archive = BytesIO()
    with ZipFile(archive, "w") as output:
        output.writestr("unrelated.txt", "not a Word document")
    assert upload(client, candidate, name="fake.docx", content=archive.getvalue()).status_code == 415
    assert list((isolated_uploads / "cvs").iterdir()) == []


def test_company_rejects_corrupted_image_and_cleans_files(client, recruitment, isolated_uploads):
    assert upload_image(client, recruitment["eh"], "logo", content=b"\x89PNG\r\n\x1a\n" + b"x" * 200).status_code == 415
    assert list((isolated_uploads / "company").iterdir()) == []


def test_upload_directory_is_relative_to_server():
    assert Path(Settings(UPLOAD_DIR="uploads/").UPLOAD_DIR) == SERVER_DIR / "uploads"


def test_database_default_timestamps_include_server_offset(monkeypatch):
    from src.config import database
    from src.models.base import ServerTimestamp
    monkeypatch.setattr(database, "SERVER_TIMEZONE", timezone(timedelta(hours=7)))
    column = ServerTimestamp()
    legacy = datetime(2026, 11, 16, 23, 30)
    mysql = SimpleNamespace(name="mysql")
    converted = column.process_result_value(legacy, mysql)
    assert converted.isoformat() == "2026-11-16T23:30:00+07:00"
    assert column.process_bind_param(converted, mysql) == legacy
    sqlite = column.process_result_value(legacy, SimpleNamespace(name="sqlite"))
    assert sqlite.utcoffset() == timedelta(0)


def test_cors_allows_frontend_and_rejects_other_origins(client):
    for origin in ("http://localhost:5500", "http://127.0.0.1:5500"):
        response = client.options("/api/v1/auth/login", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
    response = client.options("/api/v1/auth/login", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_seed_normalizes_admin_email_and_preserves_existing_password(db_session, monkeypatch):
    user, _ = actor(db_session, "ADMIN", "seed-check@example.com")
    original_hash = user.password_hash
    monkeypatch.setenv("ADMIN_EMAIL", "  SEED-CHECK@EXAMPLE.COM ")
    monkeypatch.setenv("ADMIN_PASSWORD", "Different1234")
    assert seed_admin(db_session) == "đã tồn tại"
    assert db_session.query(User).count() == 1
    assert user.password_hash == original_hash
    user.role_id = db_session.query(Role.id).filter(Role.name == "CANDIDATE").scalar()
    db_session.commit()
    assert seed_admin(db_session) == "bỏ qua (email đã thuộc tài khoản không phải ADMIN)"
    monkeypatch.delenv("ADMIN_PASSWORD")
    assert seed_admin(db_session) == "bỏ qua (chưa đặt ADMIN_EMAIL/ADMIN_PASSWORD)"
