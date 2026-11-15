"""PB-018/020/022/024/025/026: API bổ sung cho giao diện và luồng end-to-end."""
import os

import pytest

from src.config.settings import settings
from src.models import AuditLog, CV, Company, Industry, Notification, Province
from tests.test_design_api import actor, recruitment  # noqa: F401 - dùng lại fixture dữ liệu tuyển dụng

API = "/api/v1"
PDF = b"%PDF-1.4\n" + b"x" * 64


@pytest.fixture(autouse=True)
def tmp_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


def apply(client, r, **extra):
    return client.post(f"{API}/applications", headers=r["ch"],
                       json={"job_id": r["job"].id, "cv_id": r["cv"].id, **extra})


def test_public_search_matches_company_and_filters_by_company(client, recruitment):
    r = recruitment
    assert client.get(f"{API}/jobs?q=Compan").json()["total"] == 1  # tìm theo tên công ty
    assert client.get(f"{API}/jobs?q=khong-co").json()["total"] == 0
    assert client.get(f"{API}/jobs?company_id={r['job'].company_id}").json()["total"] == 1
    assert client.get(f"{API}/jobs?company_id=9999").json()["total"] == 0
    assert client.get(f"{API}/jobs?sort=salary").status_code == 200
    assert client.get(f"{API}/jobs?sort=bad").status_code == 422


def test_public_company_list_only_approved_with_open_job_count(client, db_session, recruitment):
    db_session.add(Company(name="Pending Co", slug="pending-co", status="PENDING"))
    db_session.commit()
    body = client.get(f"{API}/companies").json()
    names = [c["name"] for c in body["items"]]
    assert "Pending Co" not in names and body["total"] == 2
    assert body["items"][0]["name"] == "Company" and body["items"][0]["open_jobs"] == 1  # nhiều tin đứng trước
    assert client.get(f"{API}/companies?q=fore").json()["total"] == 1
    detail = client.get(f"{API}/companies/{recruitment['job'].company_id}").json()
    assert detail["open_jobs"] == 1 and "status" not in detail and "reject_reason" not in detail


def test_application_detail_history_and_access_control(client, recruitment):
    r = recruitment
    aid = apply(client, r, cover_letter="Xin chào").json()["id"]
    client.patch(f"{API}/applications/{aid}/status", headers=r["eh"], json={"status": "VIEWED", "note": "Đã xem"})

    mine = client.get(f"{API}/applications/{aid}", headers=r["ch"])
    assert mine.status_code == 200
    body = mine.json()
    assert body["job_title"] == "Python developer" and body["company_name"] == "Company"
    assert [h["to_status"] for h in body["history"]] == ["NEW", "VIEWED"]
    assert body["can_withdraw"] is True and body["allowed_statuses"] == []

    theirs = client.get(f"{API}/applications/{aid}", headers=r["eh"]).json()
    assert theirs["candidate_email"] == "apply@example.com" and theirs["cv_file_name"] == "cv.pdf"
    assert theirs["allowed_statuses"] == ["INTERVIEW", "REJECTED"] and theirs["can_withdraw"] is False

    assert client.get(f"{API}/applications/{aid}").status_code == 401
    assert client.get(f"{API}/applications/{aid}", headers=r["xh"]).status_code == 404  # ứng viên khác
    assert client.get(f"{API}/applications/{aid}", headers=r["oh"]).status_code == 404  # công ty khác

    listing = client.get(f"{API}/employer/jobs/{r['job'].id}/applications", headers=r["eh"]).json()
    assert listing["items"][0]["candidate_name"] == "Test user"
    assert client.get(f"{API}/employer/jobs/{r['job'].id}/applications?status=NEW", headers=r["eh"]).json()["total"] == 0
    assert client.get(f"{API}/applications/my-applications?status=VIEWED", headers=r["ch"]).json()["total"] == 1


def test_application_cv_download_restricted_and_survives_soft_delete(client, db_session, recruitment, tmp_upload_dir):
    r = recruitment
    os.makedirs(tmp_upload_dir / "cvs")
    (tmp_upload_dir / "cvs" / "test.pdf").write_bytes(PDF)
    aid = apply(client, r).json()["id"]

    assert client.get(f"{API}/applications/{aid}/cv").status_code == 401
    assert client.get(f"{API}/applications/{aid}/cv", headers=r["xh"]).status_code == 404
    assert client.get(f"{API}/applications/{aid}/cv", headers=r["oh"]).status_code == 404
    got = client.get(f"{API}/applications/{aid}/cv", headers=r["eh"])
    assert got.status_code == 200 and got.content == PDF
    assert got.headers["content-type"] == "application/pdf"

    # Ứng viên xóa CV đã nộp: chỉ xóa mềm, nhà tuyển dụng nhận đơn vẫn tải được (BR-15)
    assert client.delete(f"{API}/candidates/me/cvs/{r['cv'].id}", headers=r["ch"]).status_code == 204
    db_session.expire_all()
    assert db_session.get(CV, r["cv"].id).deleted_at is not None
    assert client.get(f"{API}/applications/{aid}/cv", headers=r["eh"]).status_code == 200
    # CV chưa nộp của người khác không thể tải qua đường dẫn trực tiếp của ứng viên khác
    assert client.get(f"{API}/candidates/me/cvs/{r['bad_cv'].id}/download", headers=r["ch"]).status_code == 404


def test_saved_jobs(client, recruitment):
    r = recruitment
    jid = r["job"].id
    assert client.put(f"{API}/saved-jobs/{jid}").status_code == 401
    assert client.put(f"{API}/saved-jobs/{jid}", headers=r["eh"]).status_code == 403
    assert client.put(f"{API}/saved-jobs/{r['draft'].id}", headers=r["ch"]).status_code == 404
    assert client.put(f"{API}/saved-jobs/{jid}", headers=r["ch"]).json()["saved"] is True
    assert client.put(f"{API}/saved-jobs/{jid}", headers=r["ch"]).status_code == 200  # lưu lại không lỗi
    assert [j["id"] for j in client.get(f"{API}/saved-jobs", headers=r["ch"]).json()["items"]] == [jid]
    assert client.get(f"{API}/saved-jobs", headers=r["xh"]).json()["total"] == 0
    assert client.delete(f"{API}/saved-jobs/{jid}", headers=r["ch"]).json()["saved"] is False
    assert client.get(f"{API}/saved-jobs", headers=r["ch"]).json()["total"] == 0


def test_notifications_unread_count_and_read_all(client, recruitment):
    r = recruitment
    aid = apply(client, r).json()["id"]
    employer_inbox = client.get(f"{API}/notifications", headers=r["eh"]).json()
    assert employer_inbox["unread_count"] == 1 and employer_inbox["items"][0]["type"] == "APPLICATION_NEW"
    client.patch(f"{API}/applications/{aid}/status", headers=r["eh"], json={"status": "INTERVIEW"})
    inbox = client.get(f"{API}/notifications", headers=r["ch"]).json()
    assert inbox["unread_count"] == 1 and "Mời phỏng vấn" in inbox["items"][0]["message"]
    assert client.patch(f"{API}/notifications/read-all").status_code == 401
    assert client.patch(f"{API}/notifications/read-all", headers=r["ch"]).json()["updated"] == 1
    assert client.get(f"{API}/notifications", headers=r["ch"]).json()["unread_count"] == 0
    assert client.get(f"{API}/notifications", headers=r["eh"]).json()["unread_count"] == 1  # không ảnh hưởng người khác


def test_end_to_end_register_profile_company_job_apply_process(client, db_session, tmp_upload_dir):
    """PB-025: đăng ký -> hồ sơ -> duyệt công ty -> đăng tin -> duyệt tin -> ứng tuyển -> xử lý đơn."""
    industry = Industry(name="Công nghệ thông tin", slug="cntt")
    province = Province(name="Hà Nội", code="HN")
    db_session.add_all([industry, province])
    db_session.commit()
    _, admin = actor(db_session, "ADMIN", "admin@example.com")

    def register(email, role):
        assert client.post(f"{API}/auth/register", json={
            "email": email, "password": "Abcd1234", "full_name": "Người dùng " + role, "role": role}).status_code == 201
        token = client.post(f"{API}/auth/login", json={"email": email, "password": "Abcd1234"}).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    employer, candidate = register("hr@example.com", "EMPLOYER"), register("dev@example.com", "CANDIDATE")

    # Ứng viên: hồ sơ + CV
    assert client.post(f"{API}/candidates/me/profile", headers=candidate,
                       json={"headline": "Backend Developer", "province_id": province.id}).status_code == 201
    cv_id = client.post(f"{API}/candidates/me/cvs", headers=candidate,
                        files={"file": ("cv.pdf", PDF, "application/pdf")}).json()["id"]

    # Nhà tuyển dụng: công ty chờ duyệt thì chưa đăng tin được
    company = client.post(f"{API}/employer/company", headers=employer, json={
        "name": "Công ty Demo", "industry_id": industry.id, "size": "51-200",
        "address": "1 Tràng Tiền", "province_id": province.id}).json()
    assert company["status"] == "PENDING"
    job_payload = {"title": "Backend Python Developer", "industry_id": industry.id, "province_id": province.id,
                   "work_address": "1 Tràng Tiền", "description": "Phát triển API cho hệ thống tuyển dụng.",
                   "requirements": "Có kinh nghiệm Python và SQL.", "benefits": "Lương tháng 13.",
                   "salary_min": 20000000, "salary_max": 35000000, "experience_level": "FROM_1_TO_3",
                   "employment_type": "FULL_TIME", "positions": 2, "deadline": "2099-12-31"}
    assert client.post(f"{API}/employer/jobs", headers=employer, json=job_payload).status_code == 403
    assert client.get(f"{API}/companies").json()["total"] == 0

    # Admin từ chối (bắt buộc lý do) -> NTD gửi lại -> Admin duyệt
    cid = company["id"]
    assert client.post(f"{API}/admin/companies/{cid}/reject", headers=admin, json={}).status_code == 422
    assert client.post(f"{API}/admin/companies/{cid}/reject", headers=admin,
                       json={"reason": "Thiếu thông tin website công ty"}).status_code == 200
    assert client.get(f"{API}/employer/company", headers=employer).json()["reject_reason"]
    assert client.post(f"{API}/employer/company/resubmit", headers=employer).json()["status"] == "PENDING"
    assert client.post(f"{API}/admin/companies/{cid}/approve", headers=admin).json()["status"] == "APPROVED"

    # Đăng tin -> gửi duyệt -> Admin duyệt -> hiển thị công khai
    job = client.post(f"{API}/employer/jobs", headers=employer, json=job_payload)
    assert job.status_code == 201, job.text
    jid = job.json()["id"]
    assert client.get(f"{API}/jobs/{jid}").status_code == 404  # nháp chưa công khai
    assert client.post(f"{API}/employer/jobs/{jid}/submit", headers=employer).json()["status"] == "PENDING"
    assert client.post(f"{API}/admin/jobs/{jid}/approve", headers=employer).status_code == 403
    assert client.post(f"{API}/admin/jobs/{jid}/approve", headers=admin).json()["status"] == "APPROVED"
    assert client.get(f"{API}/jobs?q=python").json()["items"][0]["id"] == jid
    assert client.get(f"{API}/companies").json()["items"][0]["open_jobs"] == 1

    # Ứng tuyển -> chống trùng -> NTD xử lý -> ứng viên theo dõi
    applied = client.post(f"{API}/applications", headers=candidate,
                          json={"job_id": jid, "cv_id": cv_id, "cover_letter": "Tôi phù hợp vị trí này."})
    assert applied.status_code == 201, applied.text
    aid = applied.json()["id"]
    assert client.post(f"{API}/applications", headers=candidate, json={"job_id": jid, "cv_id": cv_id}).status_code == 409
    assert client.get(f"{API}/jobs/{jid}").json()["application_count"] == 1
    assert client.get(f"{API}/applications/{aid}/cv", headers=employer).content == PDF
    for status in ("VIEWED", "INTERVIEW", "ACCEPTED"):
        assert client.patch(f"{API}/applications/{aid}/status", headers=employer,
                            json={"status": status}).status_code == 200
    assert client.patch(f"{API}/applications/{aid}/status", headers=employer,
                        json={"status": "REJECTED"}).status_code == 409  # BR-17: trạng thái cuối
    assert client.patch(f"{API}/applications/{aid}/withdraw", headers=candidate).status_code == 409
    detail = client.get(f"{API}/applications/{aid}", headers=candidate).json()
    assert detail["status"] == "ACCEPTED"
    assert [h["to_status"] for h in detail["history"]] == ["NEW", "VIEWED", "INTERVIEW", "ACCEPTED"]
    assert client.get(f"{API}/notifications", headers=candidate).json()["unread_count"] == 3

    # Đóng tin thì không nhận đơn mới, đơn cũ vẫn còn (BR-18)
    assert client.post(f"{API}/employer/jobs/{jid}/close", headers=employer).json()["status"] == "CLOSED"
    assert client.get(f"{API}/jobs/{jid}").status_code == 404
    assert client.get(f"{API}/employer/jobs/{jid}/applications", headers=employer).json()["total"] == 1
    assert db_session.query(AuditLog).count() >= 3
    assert db_session.query(Notification).count() >= 5


@pytest.mark.parametrize("method,path", [
    ("get", "/candidates/me/profile"), ("get", "/candidates/me/cvs"), ("get", "/employer/company"),
    ("get", "/employer/jobs"), ("get", "/admin/companies"), ("get", "/admin/jobs"),
    ("get", "/applications/my-applications"), ("get", "/notifications"), ("get", "/saved-jobs"),
    ("get", "/users/profile"),
])
def test_protected_endpoints_reject_anonymous_and_bad_tokens(client, method, path):
    """PB-026: mọi API cần đăng nhập đều trả 401 khi thiếu hoặc sai token."""
    assert getattr(client, method)(API + path).status_code == 401
    assert getattr(client, method)(API + path, headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_role_matrix_blocks_cross_role_access(client, db_session, recruitment):
    """PB-026: vai trò này không gọi được chức năng của vai trò khác."""
    r = recruitment
    _, admin = actor(db_session, "ADMIN", "root@example.com")
    for headers, path in [
        (r["ch"], "/employer/company"), (r["ch"], "/employer/jobs"), (r["ch"], "/admin/companies"),
        (r["ch"], "/admin/jobs"), (r["eh"], "/candidates/me/profile"), (r["eh"], "/candidates/me/cvs"),
        (r["eh"], "/admin/companies"), (r["eh"], "/admin/jobs"), (r["eh"], "/applications/my-applications"),
        (admin, "/candidates/me/cvs"), (admin, "/employer/company"), (admin, "/saved-jobs"),
    ]:
        assert client.get(API + path, headers=headers).status_code == 403, path
    assert client.get(f"{API}/admin/companies", headers=admin).status_code == 200
    assert client.get(f"{API}/admin/jobs", headers=admin).status_code == 200
