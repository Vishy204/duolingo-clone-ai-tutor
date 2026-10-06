"""XP ledger. Every XP gain is an XpEvent row stamped with the learner's (simulated) day, which
makes daily goals, streak calendars and weekly leaderboards simple aggregate queries."""
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import user_today
from app.models import User, XpEvent
from app.services import streaks


def award(db: Session, user: User, amount: int, source: str) -> bool:
    """Add XP and record daily activity. Returns True if this extended the streak today."""
    today = user_today(user.clock_offset_days)
    db.add(XpEvent(user_id=user.id, amount=amount, source=source, day=today))
    user.total_xp += amount
    return streaks.record_activity(user, today)


def xp_on(db: Session, user_id: int, day: date) -> int:
    return db.scalar(
        select(func.coalesce(func.sum(XpEvent.amount), 0)).where(XpEvent.user_id == user_id, XpEvent.day == day)
    ) or 0


def xp_today(db: Session, user: User) -> int:
    return xp_on(db, user.id, user_today(user.clock_offset_days))


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def xp_since(db: Session, user_ids: list[int], since: date, until: date) -> dict[int, int]:
    rows = db.execute(
        select(XpEvent.user_id, func.sum(XpEvent.amount))
        .where(XpEvent.user_id.in_(user_ids), XpEvent.day >= since, XpEvent.day <= until)
        .group_by(XpEvent.user_id)
    ).all()
    return {uid: int(total) for uid, total in rows}


def daily_history(db: Session, user: User, days: int = 7) -> list[dict]:
    today = user_today(user.clock_offset_days)
    start = today - timedelta(days=days - 1)
    rows = dict(
        db.execute(
            select(XpEvent.day, func.sum(XpEvent.amount))
            .where(XpEvent.user_id == user.id, XpEvent.day >= start, XpEvent.day <= today)
            .group_by(XpEvent.day)
        ).all()
    )
    return [
        {"day": (start + timedelta(days=i)).isoformat(), "xp": int(rows.get(start + timedelta(days=i), 0))}
        for i in range(days)
    ]


def active_days(db: Session, user: User, days: int = 35) -> list[str]:
    today = user_today(user.clock_offset_days)
    start = today - timedelta(days=days - 1)
    rows = db.scalars(
        select(XpEvent.day).where(XpEvent.user_id == user.id, XpEvent.day >= start).group_by(XpEvent.day)
    ).all()
    return sorted(d.isoformat() for d in rows)
