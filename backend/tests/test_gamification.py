from datetime import date, datetime, timedelta

from app.core.config import get_settings
from app.models import User
from app.services import hearts, streaks


def make_user(**kw) -> User:
    base = dict(hearts=5, hearts_updated_at=datetime(2026, 1, 1, 12), streak_count=0, longest_streak=0,
                last_active_date=None, streak_freezes=0, clock_offset_days=0, gems=500)
    base.update(kw)
    return User(**base)


def test_streak_increments_once_per_day_and_resets_after_gap():
    u = make_user()
    d = date(2026, 3, 2)
    assert streaks.record_activity(u, d) and u.streak_count == 1
    assert not streaks.record_activity(u, d) and u.streak_count == 1  # same day
    assert streaks.record_activity(u, d + timedelta(days=1)) and u.streak_count == 2
    streaks.record_activity(u, d + timedelta(days=4))  # missed 2 days
    assert u.streak_count == 1 and u.longest_streak == 2


def test_streak_freeze_covers_a_missed_day():
    u = make_user(streak_count=5, longest_streak=5, last_active_date=date(2026, 3, 1), streak_freezes=1)
    streaks.record_activity(u, date(2026, 3, 3))
    assert u.streak_count == 6 and u.streak_freezes == 0


def test_refresh_reports_lost_streak():
    u = make_user(streak_count=4, last_active_date=date(2026, 3, 1))
    events = streaks.refresh(u, date(2026, 3, 5))
    assert events == {"streak_lost": 4} and u.streak_count == 0


def test_hearts_regenerate_over_time():
    s = get_settings()
    start = datetime(2026, 1, 1, 12)
    u = make_user(hearts=2, hearts_updated_at=start)
    hearts.regenerate(u, start + timedelta(minutes=s.heart_regen_minutes * 2 + 5))
    assert u.hearts == 4
    hearts.regenerate(u, start + timedelta(days=3))
    assert u.hearts == s.max_hearts


def test_refill_costs_gems():
    u = make_user(hearts=0, hearts_updated_at=datetime.now())
    assert hearts.refill_with_gems(u)
    assert u.hearts == get_settings().max_hearts and u.gems == 500 - get_settings().refill_hearts_gem_cost
    assert not hearts.refill_with_gems(u)  # already full
