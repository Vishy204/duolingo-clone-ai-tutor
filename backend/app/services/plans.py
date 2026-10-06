"""Read-side helpers for adaptive plans (shared by the lesson engine and the API)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AdaptivePlan, Exercise, ExerciseAttempt


def latest_ready_plan(db: Session, user_id: int) -> AdaptivePlan | None:
    return db.scalar(
        select(AdaptivePlan)
        .where(AdaptivePlan.user_id == user_id, AdaptivePlan.status == "ready")
        .order_by(AdaptivePlan.id.desc())
        .limit(1)
    )


def latest_plan(db: Session, user_id: int) -> AdaptivePlan | None:
    return db.scalar(
        select(AdaptivePlan).where(AdaptivePlan.user_id == user_id).order_by(AdaptivePlan.id.desc()).limit(1)
    )


def plan_exercises(db: Session, plan: AdaptivePlan) -> list[Exercise]:
    ids = (plan.plan or {}).get("exercise_ids", [])
    if not ids:
        return []
    by_id = {e.id: e for e in db.scalars(select(Exercise).where(Exercise.id.in_(ids))).all()}
    return [by_id[i] for i in ids if i in by_id]


def unseen_plan_exercises(db: Session, plan: AdaptivePlan, user_id: int, limit: int) -> list[Exercise]:
    """Plan items the learner hasn't attempted yet (used to sprinkle Duo's picks into lessons)."""
    exercises = [e for e in plan_exercises(db, plan) if e.source == "agent"]
    if not exercises:
        return []
    seen = set(
        db.scalars(
            select(ExerciseAttempt.exercise_id).where(
                ExerciseAttempt.user_id == user_id,
                ExerciseAttempt.exercise_id.in_([e.id for e in exercises]),
            )
        )
    )
    return [e for e in exercises if e.id not in seen][:limit]
