"""Single source of "now" so streak/heart logic is testable and day-travel can be simulated.

Each learner carries `clock_offset_days`; the demo "Simulate next day" button bumps it.
"""
from datetime import UTC, date, datetime, timedelta


def utcnow() -> datetime:
    # Stored naive-UTC (SQLite has no tz support); keep it consistent everywhere.
    return datetime.now(UTC).replace(tzinfo=None)


def user_now(offset_days: int = 0) -> datetime:
    return utcnow() + timedelta(days=offset_days)


def user_today(offset_days: int = 0) -> date:
    return user_now(offset_days).date()
