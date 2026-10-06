"""Achievements (badges) and daily quests, both derived from the activity ledger."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import user_today
from app.models import Achievement, LessonSession, User, UserAchievement, UserSkillProgress
from app.services import xp as xp_service


def metrics(db: Session, user: User) -> dict[str, int]:
    def count_sessions(*conds) -> int:
        return db.scalar(
            select(func.count(LessonSession.id)).where(
                LessonSession.user_id == user.id, LessonSession.status == "completed", *conds
            )
        ) or 0

    skills = db.scalar(
        select(func.count(UserSkillProgress.id)).where(
            UserSkillProgress.user_id == user.id, UserSkillProgress.completed_at.is_not(None),
            UserSkillProgress.crowns > 0,
        )
    ) or 0
    legendary = db.scalar(
        select(func.count(UserSkillProgress.id)).where(
            UserSkillProgress.user_id == user.id, UserSkillProgress.is_legendary.is_(True)
        )
    ) or 0
    return {
        "total_xp": user.total_xp,
        "streak": max(user.longest_streak, user.streak_count),
        "lessons": count_sessions(LessonSession.mode == "lesson"),
        "perfect": count_sessions(LessonSession.mode == "lesson", LessonSession.mistake_count == 0),
        "skills": skills,
        "personalized": count_sessions(LessonSession.mode == "personalized"),
        "legendary": legendary,
    }


def check_and_unlock(db: Session, user: User) -> list[Achievement]:
    have = set(db.scalars(select(UserAchievement.achievement_id).where(UserAchievement.user_id == user.id)))
    m = metrics(db, user)
    unlocked = []
    for ach in db.scalars(select(Achievement)).all():
        if ach.id not in have and m.get(ach.metric, 0) >= ach.threshold:
            db.add(UserAchievement(user_id=user.id, achievement_id=ach.id))
            unlocked.append(ach)
    return unlocked


def list_for_user(db: Session, user: User) -> list[dict]:
    m = metrics(db, user)
    have = {
        ua.achievement_id: ua.unlocked_at
        for ua in db.scalars(select(UserAchievement).where(UserAchievement.user_id == user.id))
    }
    out = []
    for ach in db.scalars(select(Achievement).order_by(Achievement.metric, Achievement.threshold)).all():
        out.append({
            "key": ach.key, "title": ach.title, "description": ach.description,
            "color": ach.color, "progress": min(m.get(ach.metric, 0), ach.threshold), "threshold": ach.threshold,
            "unlocked": ach.id in have,
            "unlocked_at": have[ach.id].isoformat() if ach.id in have else None,
        })
    return out


def daily_quests(db: Session, user: User) -> list[dict]:
    today = user_today(user.clock_offset_days)
    todays = db.scalars(
        select(LessonSession).where(
            LessonSession.user_id == user.id, LessonSession.status == "completed", LessonSession.day == today
        )
    ).all()
    xp_today = xp_service.xp_today(db, user)
    lessons_today = sum(1 for s in todays if s.mode == "lesson")
    great_today = sum(1 for s in todays if (s.accuracy or 0) >= 0.9)
    personalized_today = sum(1 for s in todays if s.mode == "personalized")
    return [
        {"key": "xp", "title": f"Earn {user.daily_goal_xp} XP",
         "progress": min(xp_today, user.daily_goal_xp), "target": user.daily_goal_xp},
        {"key": "lessons", "title": "Complete 2 lessons", "progress": min(lessons_today, 2), "target": 2},
        {"key": "accuracy", "title": "Score 90% or higher in 2 lessons",
         "progress": min(great_today, 2), "target": 2},
        {"key": "duo", "title": "Finish a personalized practice from Smarto",
         "progress": min(personalized_today, 1), "target": 1},
    ]
