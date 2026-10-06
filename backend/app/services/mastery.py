"""Deterministic learner model: per-concept mastery + spaced repetition.

A lightweight knowledge-tracing update (exponential moving estimate) that runs synchronously on
every answer, so in-lesson adaptation never waits for an LLM. Wrong answers move the estimate
more than right ones (they are more informative), production exercises (typing/translating)
count more than recognition ones. Review intervals grow with a correct streak (1, 2, 4, 8... days)
and collapse to "now" on a mistake. The tutor agents read this table as their primary signal.
"""
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import user_now
from app.models import Exercise, User, UserConceptMastery
from app.services.exercise_types import PRODUCTION_TYPES

LR_CORRECT = 0.15
LR_WRONG = 0.30
PRODUCTION_WEIGHT = 1.3


def update_for_attempt(db: Session, user: User, exercise: Exercise, correct: bool, typo: bool) -> None:
    now = user_now(user.clock_offset_days)
    production = exercise.type in PRODUCTION_TYPES
    for concept in exercise.concepts:
        row = _get_or_create(db, user.id, concept.id)
        update_row(row, correct=correct, typo=typo, production=production, now=now)


def update_row(row: UserConceptMastery, *, correct: bool, typo: bool, production: bool, now: datetime) -> None:
    weight = PRODUCTION_WEIGHT if production else 1.0
    target = 1.0 if correct else 0.0
    lr = (LR_CORRECT if correct else LR_WRONG) * weight
    if correct and typo:
        lr *= 0.5  # right idea, sloppy spelling: smaller boost
    row.mastery = round(min(1.0, max(0.0, row.mastery + lr * (target - row.mastery))), 4)
    row.attempts += 1
    row.correct += int(correct)
    if production:
        row.production_attempts += 1
        row.production_correct += int(correct)
    else:
        row.recognition_attempts += 1
        row.recognition_correct += int(correct)
    row.correct_streak = row.correct_streak + 1 if correct else 0
    row.last_seen_at = now
    row.next_review_at = now + timedelta(days=2 ** min(row.correct_streak, 6) / 2) if correct else now


def _get_or_create(db: Session, user_id: int, concept_id: int) -> UserConceptMastery:
    row = db.scalar(
        select(UserConceptMastery).where(
            UserConceptMastery.user_id == user_id, UserConceptMastery.concept_id == concept_id
        )
    )
    if row is None:
        row = UserConceptMastery(
            user_id=user_id, concept_id=concept_id, mastery=0.3, attempts=0, correct=0,
            recognition_attempts=0, recognition_correct=0, production_attempts=0,
            production_correct=0, correct_streak=0,
        )
        db.add(row)
        db.flush()
    return row


def mastery_level(m: float) -> str:
    if m >= 0.8:
        return "strong"
    if m >= 0.55:
        return "good"
    if m >= 0.35:
        return "shaky"
    return "weak"
