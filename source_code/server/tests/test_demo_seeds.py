"""Demo data must remain compatible with the integrated recruitment rules."""
from sqlalchemy.orm import sessionmaker

from src.config.settings import settings
from src.models import Company, Job, Role, User
from src.models.company import CompanyImage
from src.seeds import demo_companies, demo_jobs, demo_media
from src.seeds import run as base_seed
from src.services import company_service


def test_demo_seeds_create_valid_jobs_and_can_be_repeated(db_session, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    for seed in (base_seed.seed_industries, base_seed.seed_provinces, base_seed.seed_skills):
        seed(db_session)
        db_session.flush()
    admin = User(email="demo-admin@example.com", full_name="Demo Admin", password_hash="unused-test-hash",
                 role_id=db_session.query(Role.id).filter(Role.name == "ADMIN").scalar())
    db_session.add(admin)
    db_session.commit()

    factory = sessionmaker(bind=db_session.get_bind())
    monkeypatch.setattr(demo_companies, "SessionLocal", factory)
    monkeypatch.setattr(demo_jobs, "SessionLocal", factory)
    monkeypatch.setattr(demo_media, "SessionLocal", factory)
    demo_companies.run()
    assert db_session.query(Company).count() == len(demo_companies.COMPANIES) == 10
    assert db_session.query(Company).filter(Company.status == "PENDING").count() == 10
    for company in db_session.query(Company).all():
        company_service.approve_company(db_session, admin, company.id)

    demo_jobs.run()
    assert db_session.query(Job).count() == len(demo_jobs.JOBS) == 43
    assert db_session.query(Job).filter(Job.status == "APPROVED").count() == 43
    demo_companies.run()
    demo_jobs.run()
    assert db_session.query(Company).count() == 10
    assert db_session.query(Job).count() == 43
    assert db_session.query(User).count() == 11

    demo_media.run()
    db_session.expire_all()
    companies = db_session.query(Company).all()
    media_urls = {company.id: (company.logo_url, company.cover_url) for company in companies}
    assert all(logo and cover for logo, cover in media_urls.values())
    assert db_session.query(CompanyImage).count() == 30
    files = {path.name for path in (tmp_path / "company").iterdir()}
    assert len(files) == 50
    demo_media.run()
    db_session.expire_all()
    assert {company.id: (company.logo_url, company.cover_url) for company in db_session.query(Company)} == media_urls
    assert db_session.query(CompanyImage).count() == 30
    assert {path.name for path in (tmp_path / "company").iterdir()} == files
