import pytest

from src.models.catalog import Skill
from src.config.settings import settings
from tests.test_design_api import actor


@pytest.mark.parametrize("kind, payload, updated_field, updated_value", [
    ("educations", {"school_name": "Đại học A", "start_date": "2020-09-01", "end_date": "2024-06-01"}, "school_name", "Đại học B"),
    ("experiences", {"company_name": "Vieco", "position": "Developer", "start_date": "2024-07-01"}, "position", "Senior Developer"),
])
def test_history_crud_and_ownership(client, db_session, kind, payload, updated_field, updated_value):
    _, candidate = actor(db_session, "CANDIDATE", "history@example.com")
    _, stranger = actor(db_session, "CANDIDATE", "other-history@example.com")
    base = "/api/v1/candidates/me/history"
    created = client.post(f"{base}/{kind}", headers=candidate, json=payload)
    assert created.status_code == 201, created.text
    entry_id = created.json()["id"]
    assert client.get(base, headers=candidate).json()[kind][0]["id"] == entry_id
    assert client.get(base, headers=stranger).json()[kind] == []
    path = f"{base}/{kind}/{entry_id}"
    assert client.put(path, headers=stranger, json=payload).status_code == 404
    assert client.delete(path, headers=stranger).status_code == 404
    result = client.put(path, headers=candidate, json={**payload, updated_field: updated_value})
    assert result.status_code == 200 and result.json()[updated_field] == updated_value
    assert client.post(f"{base}/{kind}", headers=candidate, json={**payload, "end_date": "1900-01-01"}).status_code == 422
    assert client.post(f"{base}/{kind}", headers=candidate, json={**payload, "candidate_profile_id": 999}).status_code == 422
    assert client.delete(path, headers=candidate).status_code == 204
    assert client.get(base, headers=candidate).json()[kind] == []


def test_history_skills_duplicate_hidden_and_role_guard(client, db_session):
    _, candidate = actor(db_session, "CANDIDATE", "skills@example.com")
    _, employer = actor(db_session, "EMPLOYER", "skills-hr@example.com")
    skill = Skill(name="Python")
    db_session.add(skill)
    db_session.commit()
    base = "/api/v1/candidates/me/history"
    assert client.get(base).status_code == 401
    assert client.get(base, headers=employer).status_code == 403
    data = {"skill_id": skill.id, "level": "BEGINNER"}
    first = client.post(f"{base}/skills", headers=candidate, json=data)
    assert first.status_code == 201 and first.json()["name"] == "Python"
    assert client.post(f"{base}/skills", headers=candidate, json=data).status_code == 409
    path = f"{base}/skills/{first.json()['id']}"
    assert client.put(path, headers=candidate, json={**data, "level": "ADVANCED"}).json()["level"] == "ADVANCED"
    skill.is_active = False
    db_session.commit()
    assert client.put(path, headers=candidate, json=data).status_code == 200
    assert client.delete(path, headers=candidate).status_code == 204
    assert client.post(f"{base}/skills", headers=candidate, json=data).status_code == 422


def test_avatar_upload_replace_delete_and_permissions(client, db_session, tmp_path, monkeypatch):
    from tests.test_workflows import PNG
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    _, candidate = actor(db_session, "CANDIDATE", "avatar@example.com")
    _, other = actor(db_session, "CANDIDATE", "other-avatar@example.com")
    _, employer = actor(db_session, "EMPLOYER", "avatar-hr@example.com")
    path = "/api/v1/candidates/me/avatar"
    files = {"file": ("avatar.png", PNG, "image/png")}
    assert client.post(path, headers=employer, files=files).status_code == 403
    assert client.post(path, headers=candidate, files={"file": ("bad.png", b"bad", "image/png")}).status_code == 415
    first = client.post(path, headers=candidate, files=files)
    assert first.status_code == 200
    old_url = first.json()["avatar_url"]
    assert client.get("/api/v1/auth/me", headers=candidate).json()["avatar_url"] == old_url
    assert client.get("/api/v1/auth/me", headers=other).json()["avatar_url"] is None
    second = client.post(path, headers=candidate, files=files)
    assert second.status_code == 200 and second.json()["avatar_url"] != old_url
    assert client.get("/api/v1" + old_url).status_code == 404
    assert client.delete(path, headers=candidate).json()["avatar_url"] is None
    assert list((tmp_path / "company").iterdir()) == []
