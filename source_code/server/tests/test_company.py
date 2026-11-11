import pytest

from src.models import AuditLog, Company, CompanyMember, Industry, Notification, Province, Role, User
from src.services.company_service import slugify
from src.utils.security import hash_password

EMP = "/api/v1/employer/company"
ADM = "/api/v1/admin/companies"


@pytest.fixture()
def catalog(db_session):
    industry = Industry(name="Công nghệ thông tin", slug="cntt")
    province = Province(name="Hà Nội", code="HN")
    hidden = Industry(name="Ngành ẩn", slug="an", is_active=False)
    db_session.add_all([industry, province, hidden])
    db_session.commit()
    return {"industry": industry.id, "province": province.id, "hidden": hidden.id}


@pytest.fixture()
def payload(catalog):
    return {"name": "Công ty Cổ phần Đông Á", "industry_id": catalog["industry"], "size": "51-200",
            "address": "1 Tràng Tiền", "province_id": catalog["province"],
            "website": "https://donga.vn", "description": "Giới thiệu"}


def login(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Abcd1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def employer(client, email="emp@example.com"):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "Abcd1234", "full_name": "Nha Tuyen Dung", "role": "EMPLOYER"})
    return login(client, email)


def admin(client, db_session):
    role_id = db_session.query(Role.id).filter(Role.name == "ADMIN").scalar()
    db_session.add(User(email="admin@example.com", password_hash=hash_password("Abcd1234"),
                        role_id=role_id, full_name="Admin"))
    db_session.commit()
    return login(client, "admin@example.com")


def test_slugify():
    assert slugify("Công ty Cổ phần Đông Á") == "cong-ty-co-phan-dong-a"
    assert slugify("!!!") == "cong-ty"


def test_create_and_get_company(client, db_session, payload):
    h = employer(client)
    assert client.get(EMP, headers=h).status_code == 404

    r = client.post(EMP, headers=h, json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "PENDING"  # mặc định chờ duyệt
    assert body["slug"] == "cong-ty-co-phan-dong-a"
    assert body["member_role"] == "OWNER"
    assert body["reject_reason"] is None
    assert client.get(EMP, headers=h).json()["id"] == body["id"]

    assert client.post(EMP, headers=h, json=payload).status_code == 409  # mỗi NTD một công ty

    # công ty khác trùng tên -> slug có hậu tố
    h2 = employer(client, "emp2@example.com")
    assert client.post(EMP, headers=h2, json=payload).json()["slug"] == "cong-ty-co-phan-dong-a-2"


def test_create_validation(client, payload, catalog):
    h = employer(client)
    for key in ("name", "industry_id", "size", "address", "province_id"):
        bad = {k: v for k, v in payload.items() if k != key}
        assert client.post(EMP, headers=h, json=bad).status_code == 422, key
    assert client.post(EMP, headers=h, json={**payload, "name": " "}).status_code == 422
    assert client.post(EMP, headers=h, json={**payload, "size": "lớn"}).status_code == 422
    assert client.post(EMP, headers=h, json={**payload, "website": "donga.vn"}).status_code == 422
    assert client.post(EMP, headers=h, json={**payload, "industry_id": 999}).status_code == 422
    assert client.post(EMP, headers=h, json={**payload, "industry_id": catalog["hidden"]}).status_code == 422
    assert client.post(EMP, headers=h, json={**payload, "province_id": 999}).status_code == 422


def test_cannot_set_status_via_create_or_update(client, payload):
    h = employer(client)
    body = client.post(EMP, headers=h, json={**payload, "status": "APPROVED"}).json()
    assert body["status"] == "PENDING"
    r = client.patch(EMP, headers=h, json={"status": "APPROVED", "reject_reason": "x"})
    assert r.status_code == 200 and r.json()["status"] == "PENDING"


def test_update_company(client, payload):
    h = employer(client)
    assert client.patch(EMP, headers=h, json={"name": "Mới"}).status_code == 404
    client.post(EMP, headers=h, json=payload)
    r = client.patch(EMP, headers=h, json={"name": "Đông Á Group", "website": None})
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "Đông Á Group" and r.json()["website"] is None
    assert client.patch(EMP, headers=h, json={"name": None}).status_code == 422
    assert client.patch(EMP, headers=h, json={"address": "  "}).status_code == 422


def test_member_cannot_edit(client, db_session, payload):
    h = employer(client)
    company_id = client.post(EMP, headers=h, json=payload).json()["id"]
    h2 = employer(client, "member@example.com")
    uid = db_session.query(User.id).filter(User.email == "member@example.com").scalar()
    db_session.add(CompanyMember(company_id=company_id, user_id=uid, member_role="MEMBER"))
    db_session.commit()
    assert client.get(EMP, headers=h2).json()["member_role"] == "MEMBER"
    assert client.patch(EMP, headers=h2, json={"name": "Hack"}).status_code == 403


def test_role_guards(client, db_session, payload):
    assert client.get(EMP).status_code == 401
    client.post("/api/v1/auth/register", json={
        "email": "cand@example.com", "password": "Abcd1234", "full_name": "Ung Vien", "role": "CANDIDATE"})
    hc = login(client, "cand@example.com")
    assert client.post(EMP, headers=hc, json=payload).status_code == 403

    he = employer(client)
    cid = client.post(EMP, headers=he, json=payload).json()["id"]
    assert client.get(ADM, headers=he).status_code == 403
    assert client.post(f"{ADM}/{cid}/approve", headers=he).status_code == 403
    assert client.post(f"{ADM}/{cid}/reject", headers=he, json={"reason": "a" * 20}).status_code == 403

    ha = admin(client, db_session)
    assert client.post(EMP, headers=ha, json=payload).status_code == 403


def test_approve_flow(client, db_session, payload):
    he = employer(client)
    cid = client.post(EMP, headers=he, json=payload).json()["id"]
    ha = admin(client, db_session)

    listing = client.get(ADM, headers=ha, params={"status": "PENDING"}).json()
    assert listing["total"] == 1 and listing["items"][0]["owner_email"] == "emp@example.com"
    assert client.get(ADM, headers=ha, params={"status": "APPROVED"}).json()["total"] == 0
    assert client.get(ADM, headers=ha, params={"q": "emp@"}).json()["total"] == 1
    assert client.get(ADM, headers=ha, params={"status": "WRONG"}).status_code == 422

    r = client.post(f"{ADM}/{cid}/approve", headers=ha)
    assert r.status_code == 200 and r.json()["status"] == "APPROVED"
    assert r.json()["reviewed_by"] is not None and r.json()["reviewed_at"] is not None
    assert client.get(EMP, headers=he).json()["status"] == "APPROVED"

    assert client.post(f"{ADM}/{cid}/approve", headers=ha).status_code == 409  # chỉ duyệt khi PENDING
    assert client.post(f"{ADM}/{cid}/reject", headers=ha, json={"reason": "a" * 20}).status_code == 409
    assert client.post(f"{ADM}/999/approve", headers=ha).status_code == 404

    note = db_session.query(Notification).one()
    assert note.type == "COMPANY_APPROVED" and note.reference_id == cid
    assert db_session.query(AuditLog).one().action == "COMPANY_APPROVE"


def test_reject_and_resubmit_flow(client, db_session, payload):
    he = employer(client)
    cid = client.post(EMP, headers=he, json=payload).json()["id"]
    ha = admin(client, db_session)

    assert client.post(f"{ADM}/{cid}/reject", headers=ha, json={}).status_code == 422  # bắt buộc lý do
    assert client.post(f"{ADM}/{cid}/reject", headers=ha, json={"reason": "   ngắn   "}).status_code == 422
    assert client.post(EMP + "/resubmit", headers=he).status_code == 409  # đang PENDING

    reason = "Thiếu giấy phép kinh doanh, website không hoạt động"
    r = client.post(f"{ADM}/{cid}/reject", headers=ha, json={"reason": reason})
    assert r.status_code == 200 and r.json()["status"] == "REJECTED"

    mine = client.get(EMP, headers=he).json()
    assert mine["status"] == "REJECTED" and mine["reject_reason"] == reason  # NTD xem được lý do
    note = db_session.query(Notification).one()
    assert note.type == "COMPANY_REJECTED" and reason in note.message

    # sửa khi bị từ chối không tự gửi duyệt
    assert client.patch(EMP, headers=he, json={"website": "https://donga.com.vn"}).json()["status"] == "REJECTED"
    r = client.post(EMP + "/resubmit", headers=he)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "PENDING" and r.json()["reject_reason"] is None

    assert client.post(f"{ADM}/{cid}/approve", headers=ha).json()["status"] == "APPROVED"
    actions = [a for (a,) in db_session.query(AuditLog.action).order_by(AuditLog.id)]
    assert actions == ["COMPANY_REJECT", "COMPANY_APPROVE"]


def test_get_approved_company_guard(client, db_session, payload):
    from fastapi import HTTPException
    from src.services.company_service import get_approved_company

    he = employer(client)
    cid = client.post(EMP, headers=he, json=payload).json()["id"]
    user = db_session.query(User).filter(User.email == "emp@example.com").one()
    with pytest.raises(HTTPException) as e:
        get_approved_company(db_session, user)
    assert e.value.status_code == 403

    db_session.get(Company, cid).status = "APPROVED"
    db_session.commit()
    assert get_approved_company(db_session, user).id == cid
