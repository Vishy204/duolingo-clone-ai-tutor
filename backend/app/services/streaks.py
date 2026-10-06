"""Daily streak logic. Pure functions of (user, today) so they are trivially testable, and the
demo can "time travel" via user.clock_offset_days.

Rules (Duolingo-like):
- Earning XP on a day extends the streak (once per day).
- Missing exactly the days you have streak freezes for consumes freezes and keeps the streak.
- Otherwise a gap resets the streak to 0 (and the next activity starts it at 1).
"""
from datetime import date

from app.core.clock import user_today
from app.models import User


def refresh(user: User, today: date | None = None) -> dict:
    """Apply missed-day logic on read. Returns events (e.g. freeze used / streak lost)."""
    today = today or user_today(user.clock_offset_days)
    events: dict = {}
    if user.last_active_date is None or user.streak_count == 0:
        return events
    missed = (today - user.last_active_date).days - 1
    if missed <= 0:
        return events
    if user.streak_freezes >= missed:
        user.streak_freezes -= missed
        # Freezes "fill" the missed days so the chain continues from yesterday.
        user.last_active_date = date.fromordinal(today.toordinal() - 1)
        events["freezes_used"] = missed
    else:
        events["streak_lost"] = user.streak_count
        user.streak_count = 0
    return events


def record_activity(user: User, today: date | None = None) -> bool:
    """Call when the learner earns XP. Returns True if this extended the streak today."""
    today = today or user_today(user.clock_offset_days)
    refresh(user, today)
    if user.last_active_date == today:
        return False
    if user.last_active_date is not None and (today - user.last_active_date).days == 1 and user.streak_count > 0:
        user.streak_count += 1
    else:
        user.streak_count = 1
    user.last_active_date = today
    user.longest_streak = max(user.longest_streak, user.streak_count)
    return True


def is_extended_today(user: User, today: date | None = None) -> bool:
    today = today or user_today(user.clock_offset_days)
    return user.last_active_date == today
