from datetime import date, timedelta
import pytest

from src.models import Company, CompanyMember, Industry, Notification, Province, Role, Skill, User
from src.utils.security import hash_password

EMP_JOBS = "/api/v1/employer/jobs"
ADM_JOBS = "/api/v1/admin/jobs"


@pytest.fixture()
def catalog(db_session):
    ind = Industry(name="Công nghệ thông tin", slug="cntt")
    prov = Province(name="TP. Hồ Chí Minh", code="HCM")
    skill1 = Skill(name="Python", is_active=True)
    skill2 = Skill(name="FastAPI", is_active=True)
    hidden_ind = Industry(name="Ngành ẩn", slug="an", is_active=False)
    hidden_skill = Skill(name="Skill ẩn", is_active=False)

    db_session.add_all([ind, prov, skill1, skill2, hidden_ind, hidden_skill])
    db_session.commit()
    return {
        "industry": ind.id,
        "province": prov.id,
        "skill1": skill1.id,
        "skill2": skill2.id,
        "hidden_ind": hidden_ind.id,
        "hidden_skill": hidden_skill.id,
    }


def login(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Abcd1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def create_user(db_session, email, role_name, full_name="User"):
    role_id = db_session.query(Role.id).filter(Role.name == role_name).scalar()
    user = User(
        email=email,
        password_hash=hash_password("Abcd1234"),
        role_id=role_id,
        full_name=full_name,
        is_email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def setup_company(db_session, user, status="APPROVED", name="Công ty Công nghệ Vieco"):
    import uuid
    company = Company(
        name=name,
        slug=f"vieco-{uuid.uuid4().hex[:8]}",
        status=status,
    )
    db_session.add(company)
    db_session.commit()
    member = CompanyMember(company_id=company.id, user_id=user.id, member_role="OWNER")
    db_session.add(member)
    db_session.commit()
    return company


def valid_job_payload(catalog):
    future_date = (date.today() + timedelta(days=30)).isoformat()
    return {
        "title": "Tuyển dụng Lập trình viên Python Senior",
        "industry_id": catalog["industry"],
        "province_id": catalog["province"],
        "work_address": "Tầng 5, Tòa nhà Bitexco, Q1, TP.HCM",
        "description": "Lập trình backend với Python và FastAPI, xây dựng API chất lượng cao.",
        "requirements": "Ít nhất 3 năm kinh nghiệm với Python, thành thạo SQL và RESTful APIs.",
        "benefits": "Lương tháng 13, bảo hiểm sức khỏe cao cấp, thưởng dự án.",
        "salary_min": 25000000,
        "salary_max": 45000000,
        "salary_currency": "VND",
        "experience_level": "FROM_3_TO_5",
        "employment_type": "FULL_TIME",
        "positions": 2,
        "deadline": future_date,
        "skill_ids": [catalog["skill1"], catalog["skill2"]],
    }


def test_company_not_approved_cannot_manage_job(client, db_session, catalog):
    """BR-02, BR-12: Nhà tuyển dụng chỉ được đăng/quản lý tin khi công ty đã được Admin duyệt."""
    emp_user = create_user(db_session, "emp1@example.com", "EMPLOYER")
    h = login(client, "emp1@example.com")

    # 1. Chưa có công ty -> 403
    r = client.post(EMP_JOBS, headers=h, json={"title": "Tuyển dụng Tester", "action": "draft"})
    assert r.status_code == 403
    assert "chưa thuộc công ty nào" in r.json()["detail"]

    # 2. Công ty đang PENDING -> 403
    company = setup_company(db_session, emp_user, status="PENDING")
    r = client.post(EMP_JOBS, headers=h, json={"title": "Tuyển dụng Tester", "action": "draft"})
    assert r.status_code == 403
    assert "chưa được Admin duyệt" in r.json()["detail"]

    # 3. Công ty bị REJECTED -> 403
    company.status = "REJECTED"
    db_session.commit()
    r = client.post(EMP_JOBS, headers=h, json={"title": "Tuyển dụng Tester", "action": "draft"})
    assert r.status_code == 403

    # 4. Công ty APPROVED -> thành công tạo nháp
    company.status = "APPROVED"
    db_session.commit()
    r = client.post(EMP_JOBS, headers=h, json={"title": "Tuyển dụng Tester", "action": "draft"})
    assert r.status_code == 201
    assert r.json()["status"] == "DRAFT"


def test_create_draft_and_submit_job(client, db_session, catalog):
    """FR-M2-01, FR-M2-02, BR-04: Lưu nháp và gửi duyệt tin tuyển dụng."""
    emp_user = create_user(db_session, "emp2@example.com", "EMPLOYER")
    setup_company(db_session, emp_user, status="APPROVED")
    h = login(client, "emp2@example.com")

    # Lưu nháp: chỉ cần tiêu đề
    draft_res = client.post(EMP_JOBS, headers=h, json={"title": "Lập trình viên ReactJS Nháp", "action": "draft"})
    assert draft_res.status_code == 201
    draft_data = draft_res.json()
    assert draft_data["status"] == "DRAFT"
    job_id = draft_data["id"]

    # Gửi duyệt khi chưa đủ trường -> 422
    submit_fail = client.post(f"{EMP_JOBS}/{job_id}/submit", headers=h)
    assert submit_fail.status_code == 422

    # Cập nhật đủ thông tin hợp lệ
    payload = valid_job_payload(catalog)
    update_res = client.patch(f"{EMP_JOBS}/{job_id}", headers=h, json=payload)
    assert update_res.status_code == 200

    # Gửi duyệt thành công -> PENDING
    submit_res = client.post(f"{EMP_JOBS}/{job_id}/submit", headers=h)
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "PENDING"

    # Tạo thẳng tin gửi duyệt (action="submit")
    create_submit_res = client.post(EMP_JOBS, headers=h, json={**payload, "action": "submit"})
    assert create_submit_res.status_code == 201
    assert create_submit_res.json()["status"] == "PENDING"


def test_validation_rules(client, db_session, catalog):
    """Kiểm tra validation lương, số lượng, ngày hạn nộp, danh mục."""
    emp_user = create_user(db_session, "emp3@example.com", "EMPLOYER")
    setup_company(db_session, emp_user, status="APPROVED")
    h = login(client, "emp3@example.com")
    payload = valid_job_payload(catalog)

    # Tiêu đề quá ngắn (< 5 ký tự)
    r = client.post(EMP_JOBS, headers=h, json={**payload, "title": "Dev"})
    assert r.status_code == 422

    # Lương tối thiểu > lương tối đa
    r = client.post(EMP_JOBS, headers=h, json={**payload, "salary_min": 50000000, "salary_max": 20000000})
    assert r.status_code == 422

    # Số lượng < 1
    r = client.post(EMP_JOBS, headers=h, json={**payload, "positions": 0})
    assert r.status_code == 422

    # Deadline quá khứ
    past_date = (date.today() - timedelta(days=2)).isoformat()
    r = client.post(EMP_JOBS, headers=h, json={**payload, "deadline": past_date, "action": "submit"})
    assert r.status_code == 422

    # Ngành nghề bị ẩn
    r = client.post(EMP_JOBS, headers=h, json={**payload, "industry_id": catalog["hidden_ind"]})
    assert r.status_code == 422

    # Kỹ năng bị ẩn
    r = client.post(EMP_JOBS, headers=h, json={**payload, "skill_ids": [catalog["hidden_skill"]]})
    assert r.status_code == 422


def test_admin_approve_and_edit_approved_job(client, db_session, catalog):
    """FR-M2-03, FR-M2-06: Admin duyệt tin và NTD sửa tin đã duyệt cần duyệt lại."""
    emp_user = create_user(db_session, "emp4@example.com", "EMPLOYER")
    setup_company(db_session, emp_user, status="APPROVED")
    emp_h = login(client, "emp4@example.com")

    admin_user = create_user(db_session, "admin@example.com", "ADMIN")
    adm_h = login(client, "admin@example.com")

    payload = valid_job_payload(catalog)
    create_res = client.post(EMP_JOBS, headers=emp_h, json={**payload, "action": "submit"})
    job_id = create_res.json()["id"]

    # Admin duyệt tin
    appr_res = client.post(f"{ADM_JOBS}/{job_id}/approve", headers=adm_h)
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "APPROVED"
    assert appr_res.json()["reviewed_by"] == admin_user.id
    assert appr_res.json()["published_at"] is not None

    # Kiểm tra có tạo thông báo cho NTD
    notif = db_session.query(Notification).filter(Notification.user_id == emp_user.id).first()
    assert notif is not None
    assert notif.type == "JOB_APPROVED"

    # FR-M2-03: NTD sửa nội dung chính tin đã duyệt -> chuyển về PENDING để duyệt lại
    edit_res = client.patch(
        f"{EMP_JOBS}/{job_id}",
        headers=emp_h,
        json={"title": "Tuyển dụng Senior Python Backend Lead", "salary_max": 50000000},
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["status"] == "PENDING"
    assert edit_res.json()["published_at"] is None


def test_admin_reject_and_resubmit(client, db_session, catalog):
    """FR-M2-06, BR-14: Admin từ chối tin kèm lý do và NTD sửa gửi duyệt lại."""
    emp_user = create_user(db_session, "emp5@example.com", "EMPLOYER")
    setup_company(db_session, emp_user, status="APPROVED")
    emp_h = login(client, "emp5@example.com")

    create_user(db_session, "admin2@example.com", "ADMIN")
    adm_h = login(client, "admin2@example.com")

    payload = valid_job_payload(catalog)
    job_id = client.post(EMP_JOBS, headers=emp_h, json={**payload, "action": "submit"}).json()["id"]

    # Admin từ chối không có lý do -> 422
    assert client.post(f"{ADM_JOBS}/{job_id}/reject", headers=adm_h, json={"reason": "Ngắn"}).status_code == 422

    # Admin từ chối hợp lệ
    reject_reason = "Mô tả công việc chưa rõ ràng, vui lòng bổ sung chi tiết về tech stack."
    rej_res = client.post(f"{ADM_JOBS}/{job_id}/reject", headers=adm_h, json={"reason": reject_reason})
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "REJECTED"
    assert rej_res.json()["reject_reason"] == reject_reason

    # NTD xem tin thấy lý do từ chối
    my_job = client.get(f"{EMP_JOBS}/{job_id}", headers=emp_h).json()
    assert my_job["reject_reason"] == reject_reason

    # NTD sửa lại và gửi duyệt lại (BR-14)
    client.patch(f"{EMP_JOBS}/{job_id}", headers=emp_h, json={"description": "Mô tả cập nhật đầy đủ chi tiết."})
    resubmit_res = client.post(f"{EMP_JOBS}/{job_id}/submit", headers=emp_h)
    assert resubmit_res.status_code == 200
    assert resubmit_res.json()["status"] == "PENDING"
    assert resubmit_res.json()["reject_reason"] is None


def test_close_and_reopen_job(client, db_session, catalog):
    """FR-M2-04, 3.7.1: Đóng tin tuyển dụng và mở lại tin."""
    emp_user = create_user(db_session, "emp6@example.com", "EMPLOYER")
    setup_company(db_session, emp_user, status="APPROVED")
    emp_h = login(client, "emp6@example.com")

    create_user(db_session, "admin3@example.com", "ADMIN")
    adm_h = login(client, "admin3@example.com")

    payload = valid_job_payload(catalog)
    job_id = client.post(EMP_JOBS, headers=emp_h, json={**payload, "action": "submit"}).json()["id"]
    client.post(f"{ADM_JOBS}/{job_id}/approve", headers=adm_h)

    # Đóng tin tuyển dụng
    close_res = client.post(f"{EMP_JOBS}/{job_id}/close", headers=emp_h)
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "CLOSED"
    assert close_res.json()["closed_at"] is not None

    # Mở lại tin tuyển dụng -> PENDING theo bảng 3.7.1
    reopen_res = client.post(f"{EMP_JOBS}/{job_id}/reopen", headers=emp_h)
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "PENDING"
    assert reopen_res.json()["closed_at"] is None


def test_extend_job(client, db_session, catalog):
    """FR-M2-05: Gia hạn tin tuyển dụng."""
    emp_user = create_user(db_session, "emp7@example.com", "EMPLOYER")
    setup_company(db_session, emp_user, status="APPROVED")
    emp_h = login(client, "emp7@example.com")

    payload = valid_job_payload(catalog)
    job_id = client.post(EMP_JOBS, headers=emp_h, json={**payload, "action": "submit"}).json()["id"]

    create_user(db_session, "admin4@example.com", "ADMIN")
    adm_h = login(client, "admin4@example.com")
    client.post(f"{ADM_JOBS}/{job_id}/approve", headers=adm_h)

    # Gia hạn thêm 45 ngày
    new_deadline = (date.today() + timedelta(days=45)).isoformat()
    extend_res = client.post(f"{EMP_JOBS}/{job_id}/extend", headers=emp_h, json={"deadline": new_deadline})
    assert extend_res.status_code == 200
    assert extend_res.json()["deadline"] == new_deadline


def test_admin_remove_job(client, db_session, catalog):
    """FR-M2-07: Admin gỡ tin tuyển dụng vi phạm."""
    emp_user = create_user(db_session, "emp8@example.com", "EMPLOYER")
    setup_company(db_session, emp_user, status="APPROVED")
    emp_h = login(client, "emp8@example.com")

    admin = create_user(db_session, "admin5@example.com", "ADMIN")
    adm_h = login(client, "admin5@example.com")

    payload = valid_job_payload(catalog)
    job_id = client.post(EMP_JOBS, headers=emp_h, json={**payload, "action": "submit"}).json()["id"]
    client.post(f"{ADM_JOBS}/{job_id}/approve", headers=adm_h)

    # Admin gỡ tin vi phạm
    remove_res = client.post(
        f"{ADM_JOBS}/{job_id}/remove",
        headers=adm_h,
        json={"reason": "Tin tuyển dụng có dấu hiệu thu phí người ứng tuyển trái phép."},
    )
    assert remove_res.status_code == 200
    body = remove_res.json()
    assert body["status"] == "CLOSED"
    assert body["removed_by"] == admin.id
    assert body["removal_reason"] is not None


def test_candidate_cannot_access_employer_jobs(client, db_session, catalog):
    """Phân quyền: ứng viên không được truy cập API quản lý tin của nhà tuyển dụng."""
    create_user(db_session, "cand1@example.com", "CANDIDATE")
    cand_h = login(client, "cand1@example.com")

    r = client.post(EMP_JOBS, headers=cand_h, json={"title": "Hack job"})
    assert r.status_code == 403


def test_employer_cannot_access_other_company_job(client, db_session, catalog):
    """BR-13: Nhà tuyển dụng công ty A không được xem hay sửa tin của công ty B."""
    emp_a = create_user(db_session, "empa@example.com", "EMPLOYER")
    setup_company(db_session, emp_a, status="APPROVED", name="Công ty A")
    ha = login(client, "empa@example.com")

    emp_b = create_user(db_session, "empb@example.com", "EMPLOYER")
    setup_company(db_session, emp_b, status="APPROVED", name="Công ty B")
    hb = login(client, "empb@example.com")

    # A tạo tin
    job_a_id = client.post(EMP_JOBS, headers=ha, json={"title": "Tin của công ty A", "action": "draft"}).json()["id"]

    # B truy cập tin của A -> 404
    assert client.get(f"{EMP_JOBS}/{job_a_id}", headers=hb).status_code == 404
    assert client.patch(f"{EMP_JOBS}/{job_a_id}", headers=hb, json={"title": "Sửa lén"}).status_code == 404
    assert client.post(f"{EMP_JOBS}/{job_a_id}/submit", headers=hb).status_code == 404


def test_list_and_search_jobs(client, db_session, catalog):
    """Xem danh sách tin tuyển dụng, phân trang và tìm kiếm."""
    emp = create_user(db_session, "emp_list@example.com", "EMPLOYER")
    setup_company(db_session, emp, status="APPROVED")
    h = login(client, "emp_list@example.com")

    client.post(EMP_JOBS, headers=h, json={"title": "Backend Golang Developer", "action": "draft"})
    client.post(EMP_JOBS, headers=h, json={"title": "Frontend React Developer", "action": "draft"})
    client.post(EMP_JOBS, headers=h, json={"title": "AI Engineer Python", "action": "draft"})

    # Danh sách của NTD
    res = client.get(EMP_JOBS, headers=h)
    assert res.status_code == 200
    assert res.json()["total"] == 3

    # Tìm kiếm theo từ khóa
    res_search = client.get(f"{EMP_JOBS}?q=Python", headers=h)
    assert res_search.json()["total"] == 1
    assert "Python" in res_search.json()["items"][0]["title"]
