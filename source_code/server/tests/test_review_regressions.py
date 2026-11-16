from datetime import timedelta

import pytest

from src.models import Industry, Job, Skill
from src.config.settings import Settings
from src.services.public_service import today
from test_job import catalog, create_user, login, setup_company, valid_job_payload


def prepare(client, db_session, catalog, action="submit"):
    employer = create_user(db_session, "review-employer@example.com", "EMPLOYER")
    setup_company(db_session, employer)
    admin = create_user(db_session, "review-admin@example.com", "ADMIN")
    headers = login(client, employer.email)
    admin_headers = login(client, admin.email)
    payload = valid_job_payload(catalog)
    payload["action"] = action
    response = client.post("/api/v1/employer/jobs", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"], headers, admin_headers


def test_pending_job_cannot_be_edited(client, db_session, catalog):
    job_id, headers, _ = prepare(client, db_session, catalog)
    response = client.patch(f"/api/v1/employer/jobs/{job_id}", headers=headers, json={"description": None})
    assert response.status_code == 409
    assert db_session.get(Job, job_id).description is not None


def test_approved_edit_cannot_submit_incomplete_content(client, db_session, catalog):
    job_id, headers, admin_headers = prepare(client, db_session, catalog)
    assert client.post(f"/api/v1/admin/jobs/{job_id}/approve", headers=admin_headers).status_code == 200
    response = client.patch(f"/api/v1/employer/jobs/{job_id}", headers=headers, json={"deadline": None})
    assert response.status_code == 422
    db_session.expire_all()
    assert db_session.get(Job, job_id).status == "APPROVED"
    assert db_session.get(Job, job_id).deadline is not None


def test_approval_rechecks_deadline_and_catalog(client, db_session, catalog):
    job_id, _, admin_headers = prepare(client, db_session, catalog)
    job = db_session.get(Job, job_id)
    job.deadline = today() - timedelta(days=1)
    db_session.commit()
    assert client.post(f"/api/v1/admin/jobs/{job_id}/approve", headers=admin_headers).status_code == 422
    assert job.status == "PENDING"
    job.deadline = today() + timedelta(days=10)
    db_session.get(Industry, catalog["industry"]).is_active = False
    db_session.commit()
    assert client.post(f"/api/v1/admin/jobs/{job_id}/approve", headers=admin_headers).status_code == 422


def test_submit_rechecks_catalog_hidden_after_draft(client, db_session, catalog):
    job_id, headers, _ = prepare(client, db_session, catalog, action="draft")
    db_session.get(Skill, catalog["skill1"]).is_active = False
    db_session.commit()
    assert client.post(f"/api/v1/employer/jobs/{job_id}/submit", headers=headers).status_code == 422
    assert db_session.get(Job, job_id).status == "DRAFT"


def test_expired_job_is_filtered_and_extension_requires_review(client, db_session, catalog):
    job_id, headers, admin_headers = prepare(client, db_session, catalog)
    assert client.post(f"/api/v1/admin/jobs/{job_id}/approve", headers=admin_headers).status_code == 200
    job = db_session.get(Job, job_id)
    job.deadline = today() - timedelta(days=1)
    db_session.commit()
    expired = client.get("/api/v1/employer/jobs?status=EXPIRED", headers=headers).json()
    assert [row["id"] for row in expired["items"]] == [job_id]
    assert expired["items"][0]["status"] == "EXPIRED"
    assert client.get("/api/v1/employer/jobs?status=APPROVED", headers=headers).json()["total"] == 0
    result = client.post(f"/api/v1/employer/jobs/{job_id}/extend", headers=headers,
                         json={"deadline": (today() + timedelta(days=10)).isoformat()})
    assert result.status_code == 200
    assert result.json()["status"] == "PENDING"
    assert client.get(f"/api/v1/jobs/{job_id}").status_code == 404


def test_closed_job_can_extend_then_reopen(client, db_session, catalog):
    job_id, headers, admin_headers = prepare(client, db_session, catalog)
    assert client.post(f"/api/v1/admin/jobs/{job_id}/approve", headers=admin_headers).status_code == 200
    assert client.post(f"/api/v1/employer/jobs/{job_id}/close", headers=headers).status_code == 200
    result = client.post(f"/api/v1/employer/jobs/{job_id}/extend", headers=headers,
                         json={"deadline": (today() + timedelta(days=40)).isoformat()})
    assert result.status_code == 200
    assert result.json()["status"] == "CLOSED"
    assert client.post(f"/api/v1/employer/jobs/{job_id}/reopen", headers=headers).json()["status"] == "PENDING"


def test_removed_job_cannot_be_reopened(client, db_session, catalog):
    job_id, headers, admin_headers = prepare(client, db_session, catalog)
    assert client.post(f"/api/v1/admin/jobs/{job_id}/remove", headers=admin_headers,
                       json={"reason": "Tin vi pham quy dinh"}).status_code == 200
    assert client.post(f"/api/v1/employer/jobs/{job_id}/reopen", headers=headers).status_code == 409


@pytest.mark.parametrize("changes", [
    {"work_address": "x" * 256}, {"salary_currency": "TOOLONG"},
    {"salary_max": 2**63}, {"positions": 2**31},
])
def test_job_payload_respects_mysql_column_limits(client, db_session, catalog, changes):
    job_id, headers, _ = prepare(client, db_session, catalog, action="draft")
    result = client.patch(f"/api/v1/employer/jobs/{job_id}", headers=headers, json=changes)
    assert result.status_code == 422


@pytest.mark.parametrize("secret", ["", "secret_key_default", "replace-with-a-long-random-secret"])
def test_placeholder_jwt_secret_is_rejected(secret):
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(SECRET_KEY=secret)


def test_business_date_uses_vietnam_at_utc_boundary(monkeypatch):
    from datetime import datetime, timezone
    from src.utils import dates

    class Clock:
        @staticmethod
        def now(zone):
            return datetime(2026, 11, 16, 18, tzinfo=timezone.utc).astimezone(zone)

    monkeypatch.setattr(dates, "datetime", Clock)
    assert str(dates.business_today()) == "2026-11-17"
