"""Business dates follow Vietnam, independently of the hosting server timezone."""
from datetime import datetime, timedelta, timezone

VIETNAM_TIMEZONE = timezone(timedelta(hours=7))


def business_today():
    return datetime.now(VIETNAM_TIMEZONE).date()
