"""Hearts: lose one per mistake, regenerate lazily over time (no cron needed), refill with gems.

Regeneration is computed on read from `hearts_updated_at`, so it is exact, cheap and survives
restarts: every `heart_regen_minutes` one heart comes back, up to `max_hearts`.
"""
from datetime import datetime, timedelta

from app.core.clock import user_now
from app.core.config import get_settings
from app.models import User


def regenerate(user: User, now: datetime | None = None) -> None:
    s = get_settings()
    now = now or user_now(user.clock_offset_days)
    if user.hearts >= s.max_hearts:
        user.hearts = s.max_hearts
        user.hearts_updated_at = now
        return
    period = timedelta(minutes=s.heart_regen_minutes)
    elapsed = now - user.hearts_updated_at
    if elapsed < period:
        return
    gained = int(elapsed / period)
    user.hearts = min(s.max_hearts, user.hearts + gained)
    user.hearts_updated_at = now if user.hearts >= s.max_hearts else user.hearts_updated_at + gained * period


def next_heart_at(user: User) -> datetime | None:
    s = get_settings()
    if user.hearts >= s.max_hearts:
        return None
    return user.hearts_updated_at + timedelta(minutes=s.heart_regen_minutes)


def lose_heart(user: User) -> None:
    s = get_settings()
    now = user_now(user.clock_offset_days)
    regenerate(user, now)
    if user.hearts >= s.max_hearts:
        user.hearts_updated_at = now  # regen clock starts when you drop below max
    user.hearts = max(0, user.hearts - 1)


def gain_heart(user: User, n: int = 1) -> None:
    s = get_settings()
    regenerate(user)
    user.hearts = min(s.max_hearts, user.hearts + n)


def refill_with_gems(user: User) -> bool:
    s = get_settings()
    regenerate(user)
    if user.hearts >= s.max_hearts or user.gems < s.refill_hearts_gem_cost:
        return False
    user.gems -= s.refill_hearts_gem_cost
    user.hearts = s.max_hearts
    user.hearts_updated_at = user_now(user.clock_offset_days)
    return True
