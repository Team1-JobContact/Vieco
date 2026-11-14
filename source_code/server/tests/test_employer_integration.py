"""Replay requests produced by PB-015 JavaScript against the actual PB-014 API.

Uses the existing isolated SQLite fixture, never the user's MySQL database.
"""
import json
from pathlib import Path
import shutil
import subprocess
from datetime import date, timedelta

import pytest

from src.models import Industry, JobSkill, Province, Role, Skill, User
from src.utils.security import hash_password


def frontend_requests(fields, job_id=None, submit=False):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required to exercise the frontend HTTP contract")
    script = Path(__file__).resolve().parents[2] / "client/tests/job-contract.cjs"
    result = subprocess.run(
        [node, str(script)],
        input=json.dumps(dict(fields=fields, jobId=job_id, submit=submit, submitValidation=submit)),
        text=True, encoding="utf-8", capture_output=True, timeout=20, check=True,
    )
    return json.loads(result.stdout)


def test_frontend_requests_create_reload_clear_edit_submit_and_resubmit(client, db_session):
    industry = Industry(name="Công nghệ", slug="cong-nghe")
    province = Province(name="Hà Nội", code="HN")
    skill = Skill(name="Python")
    db_session.add_all([industry, province, skill])
    db_session.commit()
    admin_role = db_session.query(Role).filter_by(name="ADMIN").one()
    db_session.add(User(email="admin.integration@example.com", full_name="Admin", role_id=admin_role.id,
                        password_hash=hash_password("Abcd1234")))
    db_session.commit()

    def login(email):
        response = client.post("/api/v1/auth/login", json=dict(email=email, password="Abcd1234"))
        assert response.status_code == 200, response.text
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    registered = client.post("/api/v1/auth/register", json=dict(
        email="employer.integration@example.com", password="Abcd1234", full_name="Nhà tuyển dụng", role="EMPLOYER"))
    assert registered.status_code == 201
    employer = login("employer.integration@example.com")
    admin = login("admin.integration@example.com")
    created_company = client.post("/api/v1/employer/company", headers=employer, json=dict(
        name="Công ty Vieco", industry_id=industry.id, province_id=province.id, size="1-50", address="Hà Nội"))
    assert created_company.status_code == 201, created_company.text
    company_id = created_company.json()["id"]
    fields = dict(title="Lập trình viên Python", industry_id=str(industry.id), province_id=str(province.id),
                  work_address="Hà Nội", description="Phát triển API với Python", requirements="Có kiến thức Python",
                  experience_level="NONE", employment_type="FULL_TIME", positions="1",
                  salary_min="100", salary_max="200", benefits="Đào tạo", deadline=(date.today() + timedelta(days=30)).isoformat())
    create_request = frontend_requests(fields)[0]

    def send(request, expected):
        response = client.request(request["method"], request["path"], headers=employer, json=request.get("body"))
        assert response.status_code == expected, response.text
        return response.json()

    # A UI gate alone is insufficient: the real API also rejects an unapproved company.
    send(create_request, 403)
    assert client.post(f"/api/v1/admin/companies/{company_id}/approve", headers=admin).status_code == 200
    draft = send(create_request, 201)
    assert draft["status"] == "DRAFT"
    job_id = draft["id"]
    db_session.add(JobSkill(job_id=job_id, skill_id=skill.id))
    db_session.commit()

    # Clearing optional fields must really persist; fields absent from the form (skills) must survive.
    fields.update(title="Python Backend đã chỉnh sửa", salary_min="", salary_max="", benefits="")
    requests = frontend_requests(fields, job_id=job_id, submit=True)
    original = send(requests[0], 200)
    assert original["title"] == draft["title"]
    edited = send(requests[1], 200)
    assert edited["title"] == fields["title"]
    assert edited["salary_min"] is None and edited["salary_max"] is None and edited["benefits"] is None
    assert [s["id"] for s in edited["skills"]] == [skill.id]
    submitted = send(requests[2], 200)
    assert submitted["id"] == job_id and submitted["status"] == "PENDING"

    reason = "Cần bổ sung thêm thông tin tuyển dụng"
    rejected = client.post(f"/api/v1/admin/jobs/{job_id}/reject", headers=admin, json={"reason": reason})
    assert rejected.status_code == 200
    reloaded = send(requests[0], 200)
    assert reloaded["status"] == "REJECTED" and reloaded["reject_reason"] == reason
    saved_rejection = send(requests[1], 200)
    assert saved_rejection["status"] == "REJECTED"
    assert send(requests[2], 200)["status"] == "PENDING"
    listing = client.get("/api/v1/employer/jobs", headers=employer).json()
    assert listing["total"] == 1, "Editing and resubmitting must not create another job"
