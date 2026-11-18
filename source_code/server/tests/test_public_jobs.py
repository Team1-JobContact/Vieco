from datetime import datetime, timedelta

import pytest

from src.models import Company, Industry, Job, JobSkill, Province, Role, Skill, User
from src.services.public_service import today
from src.utils.security import hash_password

URL = "/api/v1/jobs"


@pytest.fixture()
def data(db_session):
    s = db_session
    role_id = s.query(Role.id).filter(Role.name == "EMPLOYER").scalar()
    owner = User(email="hr@example.com", password_hash=hash_password("Abcd1234"),
                 role_id=role_id, full_name="HR")
    it, fin = Industry(name="IT", slug="it"), Industry(name="Finance", slug="finance")
    hn, hcm = Province(name="Ha Noi", code="HN"), Province(name="Ho Chi Minh", code="HCM")
    py, sql = Skill(name="Python"), Skill(name="SQL")
    acme = Company(name="Acme Corp", slug="acme", status="APPROVED")
    beta = Company(name="Beta Ltd", slug="beta", status="APPROVED")
    pending = Company(name="Pending Co", slug="pending", status="PENDING")
    s.add_all([owner, it, fin, hn, hcm, py, sql, acme, beta, pending])
    s.flush()

    now = datetime.utcnow()

    def job(title, company, n, **kw):
        base = dict(company_id=company.id, created_by=owner.id, title=title, status="APPROVED",
                    deadline=today() + timedelta(days=10 + n),
                    published_at=now - timedelta(hours=n))
        base.update(kw)
        j = Job(**base)
        s.add(j)
        s.flush()
        return j

    j = {
        "py": job("Python Backend Developer", acme, 1, industry_id=it.id, province_id=hn.id,
                  employment_type="FULL_TIME", experience_level="FROM_1_TO_3",
                  salary_min=15_000_000, salary_max=25_000_000),
        "fin": job("Financial Analyst", beta, 2, industry_id=fin.id, province_id=hcm.id,
                   employment_type="PART_TIME", experience_level="NONE",
                   salary_min=8_000_000, salary_max=12_000_000),
        "intern": job("Data Intern", acme, 3, industry_id=it.id, province_id=hcm.id,
                      employment_type="INTERNSHIP", experience_level="NONE",
                      salary_min=3_000_000, salary_max=5_000_000),
        "senior": job("Senior Java Engineer", beta, 4, industry_id=it.id, province_id=hn.id,
                      employment_type="FULL_TIME", experience_level="OVER_5",
                      salary_min=40_000_000, salary_max=60_000_000),
        "free": job("Freelance Designer", acme, 5, employment_type="FREELANCE"),
        # các tin KHÔNG được hiển thị công khai
        "draft": job("Hidden Draft Job", acme, 6, status="DRAFT"),
        "pending": job("Hidden Pending Job", acme, 6, status="PENDING"),
        "closed": job("Hidden Closed Job", acme, 6, status="CLOSED"),
        "expired": job("Hidden Expired Job", acme, 6, deadline=today() - timedelta(days=1)),
        "removed": job("Hidden Removed Job", acme, 6, removed_at=now),
        "bad_company": job("Hidden Unapproved Company Job", pending, 6),
    }
    s.add_all([JobSkill(job_id=j["py"].id, skill_id=py.id),
               JobSkill(job_id=j["py"].id, skill_id=sql.id),
               JobSkill(job_id=j["fin"].id, skill_id=sql.id)])
    s.commit()
    return dict(jobs=j, it=it, fin=fin, hn=hn, hcm=hcm, py=py, sql=sql, acme=acme, beta=beta)


def titles(resp):
    assert resp.status_code == 200, resp.text
    return [i["title"] for i in resp.json()["items"]]


def test_only_public_jobs_listed(client, data):
    body = client.get(URL).json()
    assert body["total"] == 5
    assert not any(t.startswith("Hidden") for t in titles(client.get(URL)))


def test_default_order_is_newest_first(client, data):
    assert titles(client.get(URL)) == [
        "Python Backend Developer", "Financial Analyst", "Data Intern",
        "Senior Java Engineer", "Freelance Designer"]


def test_search_by_title_company_and_skill_case_insensitive(client, data):
    assert titles(client.get(URL, params={"q": "python"})) == ["Python Backend Developer"]
    assert titles(client.get(URL, params={"q": "  BETA  "})) == ["Financial Analyst", "Senior Java Engineer"]
    assert set(titles(client.get(URL, params={"q": "sql"}))) == {"Python Backend Developer", "Financial Analyst"}
    assert titles(client.get(URL, params={"q": "khong-ton-tai"})) == []


def test_filters(client, data):
    d = data
    assert set(titles(client.get(URL, params={"industry_id": d["it"].id}))) == {
        "Python Backend Developer", "Data Intern", "Senior Java Engineer"}
    assert set(titles(client.get(URL, params={"province_id": d["hcm"].id}))) == {
        "Financial Analyst", "Data Intern"}
    assert titles(client.get(URL, params={"employment_type": "INTERNSHIP"})) == ["Data Intern"]
    assert set(titles(client.get(URL, params={"experience_level": "NONE"}))) == {
        "Financial Analyst", "Data Intern"}
    assert set(titles(client.get(URL, params={"skill_id": d["sql"].id}))) == {
        "Python Backend Developer", "Financial Analyst"}
    assert set(titles(client.get(URL, params={"company_id": d["beta"].id}))) == {
        "Financial Analyst", "Senior Java Engineer"}


def test_combined_filters(client, data):
    r = client.get(URL, params={"industry_id": data["it"].id, "province_id": data["hn"].id,
                                "employment_type": "FULL_TIME"})
    assert set(titles(r)) == {"Python Backend Developer", "Senior Java Engineer"}
    r = client.get(URL, params={"q": "java", "industry_id": data["it"].id, "experience_level": "OVER_5"})
    assert titles(r) == ["Senior Java Engineer"]


def test_salary_filter_overlaps_range(client, data):
    assert titles(client.get(URL, params={"salary_min": 30_000_000})) == ["Senior Java Engineer"]
    assert set(titles(client.get(URL, params={"salary_max": 9_000_000}))) == {
        "Financial Analyst", "Data Intern"}
    r = client.get(URL, params={"salary_min": 10_000_000, "salary_max": 20_000_000})
    assert set(titles(r)) == {"Python Backend Developer", "Financial Analyst"}


def test_invalid_salary_range_rejected(client, data):
    assert client.get(URL, params={"salary_min": 20, "salary_max": 10}).status_code == 422


def test_sorting(client, data):
    assert titles(client.get(URL, params={"sort": "salary"}))[:2] == [
        "Senior Java Engineer", "Python Backend Developer"]
    assert titles(client.get(URL, params={"sort": "deadline"}))[0] == "Python Backend Developer"
    assert client.get(URL, params={"sort": "random"}).status_code == 422


def test_pagination(client, data):
    p1 = client.get(URL, params={"page_size": 2, "page": 1}).json()
    assert (p1["total"], p1["total_pages"], p1["page"], p1["page_size"]) == (5, 3, 1, 2)
    assert len(p1["items"]) == 2
    p3 = client.get(URL, params={"page_size": 2, "page": 3}).json()
    assert len(p3["items"]) == 1
    assert client.get(URL, params={"page_size": 2, "page": 4}).json()["items"] == []

    seen = []
    for page in (1, 2, 3):
        seen += titles(client.get(URL, params={"page_size": 2, "page": page}))
    assert len(seen) == len(set(seen)) == 5  # không trùng, không sót


def test_pagination_and_param_validation(client, data):
    for params in ({"page": 0}, {"page_size": 0}, {"page_size": 101}, {"industry_id": 0},
                   {"employment_type": "WRONG"}, {"experience_level": "WRONG"},
                   {"salary_min": -1}, {"q": "x" * 101}):
        assert client.get(URL, params=params).status_code == 422, params


def test_list_is_public_without_login(client, data):
    assert client.get(URL).status_code == 200


def test_job_detail(client, data):
    job = data["jobs"]["py"]
    r = client.get(f"{URL}/{job.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Python Backend Developer"
    assert body["company_name"] == "Acme Corp"
    assert body["industry_name"] == "IT" and body["province_name"] == "Ha Noi"
    assert {s["name"] for s in body["skills"]} == {"Python", "SQL"}
    assert body["view_count"] == 1
    assert client.get(f"{URL}/{job.id}").json()["view_count"] == 2


@pytest.mark.parametrize("key", ["draft", "pending", "closed", "expired", "removed", "bad_company"])
def test_detail_of_non_public_job_is_404(client, data, key):
    assert client.get(f"{URL}/{data['jobs'][key].id}").status_code == 404


def test_detail_not_found_and_invalid_id(client, data):
    assert client.get(f"{URL}/999999").status_code == 404
    assert client.get(f"{URL}/abc").status_code == 422
