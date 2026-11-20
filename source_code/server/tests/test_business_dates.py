from datetime import date, datetime, timezone

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.schemas.candidate import ProfileCreate
from src.schemas.job import JobExtendRequest
from src.services import job_service, public_service
from src.utils import dates


@pytest.fixture()
def vietnam_after_midnight(monkeypatch):
    class Clock:
        @staticmethod
        def now(tz):
            return datetime(2026, 11, 17, 18, 30, tzinfo=timezone.utc).astimezone(tz)

    monkeypatch.setattr(dates, "datetime", Clock)


def test_deadline_and_public_listing_share_vietnam_date(vietnam_after_midnight):
    assert public_service.today() == date(2026, 11, 18)
    with pytest.raises(ValidationError):
        JobExtendRequest(deadline="2026-11-17")
    assert JobExtendRequest(deadline="2026-11-18").deadline == date(2026, 11, 18)
    fields = dict(title="Backend Python", industry_id=1, province_id=1, description="Develop the backend",
                  requirements="Python and SQL experience", employment_type="FULL_TIME", experience_level="NONE",
                  salary_min=None, salary_max=None, positions=1)
    with pytest.raises(HTTPException) as error:
        job_service._validate_job_submission(**fields, deadline=date(2026, 11, 17))
    assert error.value.status_code == 422
    job_service._validate_job_submission(**fields, deadline=date(2026, 11, 18))


def test_birth_date_uses_same_business_day(vietnam_after_midnight):
    assert ProfileCreate(date_of_birth="2026-11-17").date_of_birth == date(2026, 11, 17)
    with pytest.raises(ValidationError):
        ProfileCreate(date_of_birth="2026-11-18")
