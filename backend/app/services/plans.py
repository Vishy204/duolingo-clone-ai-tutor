"""Read-side helpers for adaptive plans (shared by the lesson engine and the API)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AdaptivePlan, Exercise, ExerciseAttempt

# Practices the learner asked for (Custom Practice tab, chat, voice) form their own family: they stay
# available in the Custom Practice tab and never replace, or get replaced by, the automatic plan that
# powers the Smarto's Practice node on the path.
CUSTOM_TRIGGERS = ("custom", "chat", "voice")


def is_custom(plan: AdaptivePlan) -> bool:
    return plan.trigger in CUSTOM_TRIGGERS


def _family(custom: bool):
    col = AdaptivePlan.trigger
    return col.in_(CUSTOM_TRIGGERS) if custom else col.not_in(CUSTOM_TRIGGERS)


def latest_ready_plan(db: Session, user_id: int, custom: bool = False) -> AdaptivePlan | None:
    return db.scalar(
        select(AdaptivePlan)
        .where(AdaptivePlan.user_id == user_id, AdaptivePlan.status == "ready", _family(custom))
        .order_by(AdaptivePlan.id.desc())
        .limit(1)
    )


def latest_plan(db: Session, user_id: int, custom: bool = False) -> AdaptivePlan | None:
    return db.scalar(
        select(AdaptivePlan).where(AdaptivePlan.user_id == user_id, _family(custom))
        .order_by(AdaptivePlan.id.desc()).limit(1)
    )


def custom_plans(db: Session, user_id: int, limit: int = 12) -> list[AdaptivePlan]:
    return list(db.scalars(
        select(AdaptivePlan).where(AdaptivePlan.user_id == user_id, _family(True))
        .order_by(AdaptivePlan.id.desc()).limit(limit)
    ))


def supersede_older(db: Session, plan: AdaptivePlan) -> None:
    """A new automatic plan replaces the previous automatic one. Custom practices are kept."""
    if is_custom(plan):
        return
    for old in db.scalars(
        select(AdaptivePlan).where(
            AdaptivePlan.user_id == plan.user_id, AdaptivePlan.status == "ready",
            AdaptivePlan.id != plan.id, _family(False),
        )
    ):
        old.status = "superseded"


def plan_exercises(db: Session, plan: AdaptivePlan) -> list[Exercise]:
    ids = (plan.plan or {}).get("exercise_ids", [])
    if not ids:
        return []
    by_id = {e.id: e for e in db.scalars(select(Exercise).where(Exercise.id.in_(ids))).all()}
    return [by_id[i] for i in ids if i in by_id]


def unseen_plan_exercises(db: Session, plan: AdaptivePlan, user_id: int, limit: int) -> list[Exercise]:
    """Plan items the learner hasn't attempted yet (used to sprinkle Smarto's picks into lessons)."""
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
