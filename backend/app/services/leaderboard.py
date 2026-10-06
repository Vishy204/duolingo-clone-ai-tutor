"""Weekly league. Seeded learners ("bots") keep earning XP: their activity is topped up lazily,
deterministically per (bot, day), whenever someone views the leaderboard, so the league feels
alive without a scheduler. Each guest competes against the seeded league (cohort of 1 + bots)."""
import random
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import user_today
from app.models import User, XpEvent
from app.services import xp as xp_service

LEAGUE = {"name": "Bronze League", "color": "#CD7F32", "promote": 5, "demote": 3}


def _ensure_bot_activity(db: Session, bots: list[User], start: date, until: date) -> None:
    existing = set(
        db.execute(
            select(XpEvent.user_id, XpEvent.day).where(
                XpEvent.user_id.in_([b.id for b in bots]), XpEvent.day >= start, XpEvent.day <= until
            )
        ).all()
    )
    for bot in bots:
        base = (bot.settings or {}).get("daily_xp", 20)
        d = start
        while d <= until:
            if (bot.id, d) not in existing:
                rng = random.Random(bot.id * 100_003 + d.toordinal())
                amount = 0 if rng.random() < 0.15 else max(5, int(base * rng.uniform(0.5, 1.6)) // 5 * 5)
                # Today's XP accrues during the day: only a share is "earned" so far.
                if d == until:
                    amount = amount // 2 // 5 * 5
                if amount:
                    db.add(XpEvent(user_id=bot.id, amount=amount, source="lesson", day=d))
                else:
                    db.add(XpEvent(user_id=bot.id, amount=0, source="idle", day=d))
            d += timedelta(days=1)
    db.flush()


def weekly(db: Session, viewer: User) -> dict:
    today = user_today(viewer.clock_offset_days)
    start = xp_service.week_start(today)
    bots = db.scalars(select(User).where(User.is_bot.is_(True))).all()
    _ensure_bot_activity(db, bots, start, today)
    members = [*bots, viewer]
    totals = xp_service.xp_since(db, [m.id for m in members], start, today)
    rows = sorted(members, key=lambda m: (-totals.get(m.id, 0), m.id != viewer.id, m.display_name))
    days_left = 6 - today.weekday()
    return {
        "league": LEAGUE,
        "week_start": start.isoformat(),
        "days_left": days_left,
        "rows": [
            {
                "rank": i + 1,
                "user_id": m.id,
                "name": m.display_name,
                "avatar_color": m.avatar_color,
                "xp": totals.get(m.id, 0),
                "is_me": m.id == viewer.id,
                "streak": m.streak_count,
            }
            for i, m in enumerate(rows)
        ],
    }
