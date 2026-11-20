"""Calendar dates used by the Vietnamese recruitment workflow."""
from datetime import datetime, timedelta, timezone

BUSINESS_TIMEZONE = timezone(timedelta(hours=7))


def business_today():
    return datetime.now(BUSINESS_TIMEZONE).date()
