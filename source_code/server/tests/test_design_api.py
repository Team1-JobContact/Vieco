from datetime import timedelta
from urllib.parse import parse_qs, urlsplit
import re
import pytest
from src.config.settings import settings
from src.config import mailer
from src.models import (ApplicationStatusHistory, CandidateProfile, Company, CompanyMember, CV,
    EmailVerification, Job, Notification, PasswordReset, Role, User)
from src.services.auth_service import _utcnow
from src.services.public_service import today
from src.utils.security import create_access_token, hash_password


def actor(db, role, email):
    role_id = db.query(Role.id).filter(Role.name == role).scalar()
    user = User(email=email, password_hash=hash_password("Abcd1234"), role_id=role_id, full_name="Test user")
    db.add(user)
    db.commit()
    return user, {"Authorization": "Bearer " + create_access_token(user.id,role)}


@pytest.fixture()
def smtp(monkeypatch):
    sent = []
    monkeypatch.setattr(settings,"SMTP_HOST","smtp.example.com")
    monkeypatch.setattr(mailer,"send_email",lambda *args: sent.append(args))
    return sent


def token_from_mail(message):
    url = re.search(r"https?://[^\s]+", message[2]).group()
    return parse_qs(urlsplit(url).query)["token"][0]


def test_email_verification_reset_and_old_session_revocation(client,db_session,smtp):
    registration = client.post("/api/v1/auth/register",json={"email":"verify@example.com", "password":"Abcd1234", "full_name":"Test user"})
    assert registration.status_code == 201
    token = token_from_mail(smtp[-1])
    assert db_session.query(EmailVerification).one().token != token
    assert client.post("/api/v1/auth/verify-email",json={"token":token}).status_code == 200
    assert db_session.query(User).one().is_email_verified
    assert client.post("/api/v1/auth/verify-email",json={"token":token}).status_code == 400
    login = client.post("/api/v1/auth/login",json={"email":"verify@example.com","password":"Abcd1234"})
    old = {"Authorization":"Bearer "+login.json()["access_token"]}
    assert client.post("/api/v1/auth/forgot-password",json={"email":"verify@example.com"}).status_code == 200
    reset = token_from_mail(smtp[-1])
    assert db_session.query(PasswordReset).one().token != reset
    assert client.post("/api/v1/auth/reset-password",json={"token":reset,"password":"short"}).status_code == 422
    assert client.post("/api/v1/auth/reset-password",json={"token":reset,"password":"NewPass123"}).status_code == 200
    assert client.get("/api/v1/users/profile",headers=old).status_code == 401
    assert client.post("/api/v1/auth/reset-password",json={"token":reset,"password":"NewPass123"}).status_code == 400
    assert client.post("/api/v1/auth/login",json={"email":"verify@example.com","password":"Abcd1234"}).status_code == 401
    new = client.post("/api/v1/auth/login",json={"email":"verify@example.com","password":"NewPass123"})
    assert new.status_code == 200
    assert client.get("/api/v1/users/profile",headers={"Authorization":"Bearer "+new.json()["access_token"]}).status_code == 200
    assert client.post("/api/v1/auth/forgot-password",json={"email":"unknown@example.com"}).json() == {"message":"Nếu tài khoản tồn tại, email đặt lại mật khẩu sẽ được gửi"}


def test_expired_email_and_reset_tokens_rejected(client,db_session):
    from src.services.email_service import digest
    user,_ = actor(db_session,"CANDIDATE","expired@example.com")
    token="long-invalid-token-1234567890"
    for model in (EmailVerification,PasswordReset):
        db_session.add(model(user_id=user.id,token=digest(token),expires_at=_utcnow()-timedelta(seconds=1)))
    db_session.commit()
    assert client.post("/api/v1/auth/verify-email",json={"token":token}).status_code == 400
    assert client.post("/api/v1/auth/reset-password",json={"token":token,"password":"Abcd1234"}).status_code == 400


def test_profile_categories_and_canonical_approval(client,db_session):
    _, admin = actor(db_session,"ADMIN","admin-api@example.com")
    _, employer = actor(db_session,"EMPLOYER","employer-api@example.com")
    _, candidate = actor(db_session,"CANDIDATE","candidate-api@example.com")
    assert client.get("/api/v1/users/profile").status_code == 401
    assert client.put("/api/v1/users/profile",headers=employer,json={"headline":"Test"}).status_code == 403
    assert client.put("/api/v1/users/profile",headers=candidate,json={"headline":"Developer"}).status_code == 200
    assert client.get("/api/v1/users/profile",headers=candidate).json()["profile"]["headline"] == "Developer"
    assert client.post("/api/v1/admin/categories",headers=candidate,json={"type":"skills","name":"Python"}).status_code == 403
    industry = client.post("/api/v1/admin/categories",headers=admin,json={"type":"industries","name":"Technology"})
    assert industry.status_code == 201, industry.text
    province = client.post("/api/v1/admin/categories",headers=admin,json={"type":"provinces","name":"Ha Noi","code":"HN"})
    assert province.status_code == 201
    assert client.post("/api/v1/admin/categories",headers=admin,json={"type":"skills","name":"Python","industry_id":industry.json()["id"]}).status_code == 201
    assert len(client.get("/api/v1/categories").json()["skills"]) == 1
    assert client.post("/api/v1/admin/categories",headers=admin,json={"type":"skills","name":"Python"}).status_code == 409
    assert client.post("/api/v1/admin/categories",headers=admin,json={"type":"provinces","name":"Missing code"}).status_code == 422
    company = client.post("/api/v1/companies",headers=employer,json={"name":"Test Company","industry_id":industry.json()["id"],"province_id":province.json()["id"],"address":"1 Test Street","size":"1-50"})
    assert company.status_code == 201, company.text
    cid=company.json()["id"]
    assert client.get(f"/api/v1/companies/{cid}").status_code == 404
    assert client.patch(f"/api/v1/admin/companies/{cid}/approval",headers=admin,json={"status":"REJECTED"}).status_code == 422
    assert client.patch(f"/api/v1/admin/companies/{cid}/approval",headers=candidate,json={"status":"APPROVED"}).status_code == 403
    assert client.patch(f"/api/v1/admin/companies/{cid}/approval",headers=admin,json={"status":"APPROVED"}).status_code == 200
    assert "reviewed_by" not in client.get(f"/api/v1/companies/{cid}").json()
    job = client.post("/api/v1/jobs",headers=employer,json={"title":"Draft vacancy"})
    assert job.status_code == 201
    jid=job.json()["id"]
    assert client.patch(f"/api/v1/jobs/{jid}",headers=employer,json={"title":"Updated vacancy"}).status_code == 200
    # Canonical approval uses the same submission requirements and state machine as legacy endpoints.
    assert client.patch(f"/api/v1/admin/jobs/{jid}/approval",headers=admin,json={"status":"APPROVED"}).status_code == 400


@pytest.fixture()
def recruitment(db_session):
    emp,eh = actor(db_session,"EMPLOYER","owner@example.com")
    other,oh = actor(db_session,"EMPLOYER","foreign@example.com")
    candidate,ch = actor(db_session,"CANDIDATE","apply@example.com")
    outsider,xh = actor(db_session,"CANDIDATE","outsider@example.com")
    company=Company(name="Company",slug="company",status="APPROVED")
    foreign=Company(name="Foreign",slug="foreign",status="APPROVED")
    db_session.add_all([company,foreign]); db_session.flush()
    db_session.add_all([CompanyMember(company_id=company.id,user_id=emp.id,member_role="OWNER"),CompanyMember(company_id=foreign.id,user_id=other.id,member_role="OWNER")])
    profile=CandidateProfile(user_id=candidate.id)
    foreign_profile=CandidateProfile(user_id=outsider.id)
    db_session.add_all([profile,foreign_profile]); db_session.flush()
    cv=CV(candidate_profile_id=profile.id,file_name="cv.pdf",file_url="cvs/test.pdf",file_size=100)
    bad_cv=CV(candidate_profile_id=foreign_profile.id,file_name="foreign.pdf",file_url="cvs/foreign.pdf",file_size=100)
    job=Job(company_id=company.id,created_by=emp.id,title="Python developer",status="APPROVED",deadline=today()+timedelta(days=10))
    draft=Job(company_id=company.id,created_by=emp.id,title="Private draft",status="DRAFT")
    expired=Job(company_id=company.id,created_by=emp.id,title="Old vacancy",status="APPROVED",deadline=today()-timedelta(days=1))
    db_session.add_all([cv,bad_cv,job,draft,expired]); db_session.commit()
    return dict(eh=eh,oh=oh,ch=ch,xh=xh,job=job,draft=draft,expired=expired,cv=cv,bad_cv=bad_cv,candidate=candidate)


def test_public_visibility_pagination_and_view_count(client,recruitment):
    r=recruitment
    jobs=client.get("/api/v1/jobs?q=Python&page_size=1").json()
    assert jobs["total"] == 1 and jobs["items"][0]["id"] == r["job"].id
    assert client.get("/api/v1/jobs?page=0").status_code == 422
    assert client.get(f"/api/v1/jobs/{r['draft'].id}").status_code == 404
    assert client.get(f"/api/v1/jobs/{r['expired'].id}").status_code == 404
    assert client.get(f"/api/v1/jobs/{r['job'].id}").json()["view_count"] == 1
    assert client.get(f"/api/v1/jobs/{r['job'].id}").json()["view_count"] == 2


def test_application_ownership_transitions_notifications_and_duplicate(client,db_session,recruitment):
    r=recruitment; jid=r["job"].id
    payload={"job_id":jid,"cv_id":r["cv"].id,"cover_letter":"Please review"}
    assert client.post("/api/v1/applications",json=payload).status_code == 401
    assert client.post("/api/v1/applications",headers=r["eh"],json=payload).status_code == 403
    assert client.post("/api/v1/applications",headers=r["ch"],json={**payload,"cv_id":r["bad_cv"].id}).status_code == 404
    app=client.post("/api/v1/applications",headers=r["ch"],json=payload)
    assert app.status_code == 201, app.text
    application = app.json()
    assert application["job_id"] == jid
    assert application["cv_id"] == payload["cv_id"]
    assert application["cover_letter"] == payload["cover_letter"]
    assert application["status"] == "NEW"
    aid = application["id"]
    assert client.post("/api/v1/applications",headers=r["ch"],json=payload).status_code == 409
    assert client.get("/api/v1/applications/my-applications",headers=r["xh"]).json()["total"] == 0
    assert client.get("/api/v1/applications/my-applications",headers=r["ch"]).json()["total"] == 1
    assert client.get(f"/api/v1/employer/jobs/{jid}/applications",headers=r["oh"]).status_code == 404
    assert client.get(f"/api/v1/employer/jobs/{jid}/applications",headers=r["eh"]).json()["total"] == 1
    assert client.patch(f"/api/v1/applications/{aid}/status",headers=r["oh"],json={"status":"INTERVIEW"}).status_code == 404
    assert client.patch(f"/api/v1/applications/{aid}/status",headers=r["eh"],json={"status":"ACCEPTED"}).status_code == 409
    assert client.patch(f"/api/v1/applications/{aid}/status",headers=r["eh"],json={"status":"INTERVIEW"}).status_code == 200
    assert client.patch(f"/api/v1/applications/{aid}/withdraw",headers=r["ch"]).status_code == 409
    assert client.patch(f"/api/v1/applications/{aid}/status",headers=r["eh"],json={"status":"ACCEPTED"}).status_code == 200
    assert db_session.query(ApplicationStatusHistory).count() == 3
    notifications=client.get("/api/v1/notifications",headers=r["ch"]).json()
    nid=notifications["items"][0]["id"]
    assert client.patch(f"/api/v1/notifications/{nid}/read",headers=r["xh"]).status_code == 404
    first=client.patch(f"/api/v1/notifications/{nid}/read",headers=r["ch"])
    assert first.json()["is_read"] is True
    assert client.patch(f"/api/v1/notifications/{nid}/read",headers=r["ch"]).json()["read_at"] == first.json()["read_at"]


def test_application_rejects_closed_job(client, db_session, recruitment):
    job = recruitment["job"]
    job.status = "CLOSED"
    db_session.commit()

    headers = recruitment["ch"]
    payload = {"job_id": job.id, "cv_id": recruitment["cv"].id}
    response = client.post("/api/v1/applications", headers=headers, json=payload)
    assert response.status_code == 409
    assert client.get("/api/v1/applications/my-applications", headers=headers).json()["total"] == 0


def test_withdraw_is_owned_and_final(client,recruitment):
    r=recruitment
    app=client.post("/api/v1/applications",headers=r["ch"],json={"job_id":r["job"].id,"cv_id":r["cv"].id}).json()
    aid=app["id"]
    assert client.patch(f"/api/v1/applications/{aid}/withdraw",headers=r["xh"]).status_code == 404
    assert client.patch(f"/api/v1/applications/{aid}/withdraw",headers=r["ch"]).json()["status"] == "WITHDRAWN"
    assert client.patch(f"/api/v1/applications/{aid}/status",headers=r["eh"],json={"status":"VIEWED"}).status_code == 409
    assert client.post("/api/v1/applications",headers=r["ch"],json={"job_id":r["expired"].id,"cv_id":r["cv"].id}).status_code == 409


def test_smtp_event_failure_keeps_application_and_records_failed_delivery(client,db_session,recruitment,monkeypatch):
    r=recruitment
    monkeypatch.setattr(settings,"SMTP_HOST","smtp.example.com")
    def fail(*args):
        raise OSError("offline")
    monkeypatch.setattr(mailer,"send_email",fail)
    response=client.post("/api/v1/applications",headers=r["ch"],json={"job_id":r["job"].id,"cv_id":r["cv"].id})
    assert response.status_code == 201
    assert db_session.query(Notification).one().email_status == "FAILED"
    monkeypatch.setattr(mailer,"send_email",lambda *args: None)
    aid=response.json()["id"]
    assert client.patch(f"/api/v1/applications/{aid}/status",headers=r["eh"],json={"status":"INTERVIEW"}).status_code == 200
    row=db_session.query(Notification).filter(Notification.user_id == r["candidate"].id).one()
    assert row.email_status == "SENT" and row.email_sent_at is not None


def test_all_word_core_endpoints_exist_in_openapi(client):
    from pathlib import Path
    import zipfile
    import xml.etree.ElementTree as ET
    reference = Path(__file__).resolve().parents[3] / "docs/JobContact_System_Architecture_and_APIs.docx"
    ns = {"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(reference) as archive:
        xml = ET.fromstring(archive.read("word/document.xml"))
    expected = []
    for row in xml.findall(".//w:tr",ns):
        cells = ["".join(t.text or "" for t in c.findall(".//w:t",ns)) for c in row.findall("w:tc",ns)]
        if len(cells)>1 and cells[0] in ("GET","POST","PUT","PATCH","DELETE"):
            expected.append((cells[0],cells[1]))
    normalize = lambda url: re.sub(r"\{[^}]+\}|:[^/]+","{id}",url)
    schema = client.get("/openapi.json").json()
    actual = {(method.upper(),normalize(url)) for url,methods in schema["paths"].items() for method in methods}
    assert len(expected) == 24
    assert {(method,normalize(url)) for method,url in expected} <= actual
