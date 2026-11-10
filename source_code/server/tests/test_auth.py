from fastapi import Depends

from src.app import app
from src.middlewares.auth import require_roles
from src.models import User
from src.utils.security import verify_password

VALID = {"email": "User@Example.com", "password": "Abcd1234",
         "full_name": "Nguyen Van A", "phone": "0901234567", "role": "CANDIDATE"}


def register(client, **overrides):
    return client.post("/api/v1/auth/register", json={**VALID, **overrides})


def login(client, email="user@example.com", password="Abcd1234"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_header(client):
    register(client)
    return {"Authorization": f"Bearer {login(client).json()['access_token']}"}


def test_register_success_and_password_hashed(client, db_session):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "user@example.com"
    assert body["role"] == "CANDIDATE"
    assert "password" not in body and "password_hash" not in body

    user = db_session.query(User).one()
    assert user.password_hash != VALID["password"]
    assert verify_password(VALID["password"], user.password_hash)


def test_register_duplicate_email(client):
    assert register(client).status_code == 201
    assert register(client, email="user@example.com").status_code == 409


def test_register_validation(client):
    assert register(client, email="not-an-email").status_code == 422
    assert register(client, password="short1").status_code == 422
    assert register(client, password="onlyletters").status_code == 422
    assert register(client, full_name=" ").status_code == 422
    assert register(client, phone="abc").status_code == 422
    assert register(client, role="ADMIN").status_code == 422


def test_login_success(client, db_session):
    register(client)
    r = login(client)
    assert r.status_code == 200
    assert r.json()["access_token"]
    assert r.json()["user"]["role"] == "CANDIDATE"
    assert db_session.query(User).one().last_login_at is not None


def test_login_wrong_password_or_email(client):
    register(client)
    assert login(client, password="Wrong1234").status_code == 401
    assert login(client, email="nobody@example.com").status_code == 401


def test_login_locks_after_5_failures(client):
    register(client)
    for _ in range(5):
        assert login(client, password="Wrong1234").status_code == 401
    assert login(client).status_code == 429  # đúng mật khẩu nhưng đang bị khóa tạm


def test_locked_account_cannot_login(client, db_session):
    register(client)
    db_session.query(User).one().status = "LOCKED"
    db_session.commit()
    assert login(client).status_code == 403


def test_me_requires_valid_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer bad"}).status_code == 401


def test_me_and_logout_revokes_token(client):
    h = auth_header(client)
    assert client.get("/api/v1/auth/me", headers=h).json()["email"] == "user@example.com"
    assert client.post("/api/v1/auth/logout", headers=h).status_code == 200
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401


def test_role_guard(client):
    @app.get("/_test/admin-only")
    def admin_only(_=Depends(require_roles("ADMIN"))):
        return {"ok": True}

    h = auth_header(client)  # CANDIDATE
    assert client.get("/_test/admin-only", headers=h).status_code == 403
    assert client.get("/_test/admin-only").status_code == 401
