"""Activity log: lesson sessions, every exercise attempt, and XP events (the ledger behind
streaks, daily goals and the weekly leaderboard)."""
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import utcnow
from app.core.db import Base


class LessonSession(Base):
    __tablename__ = "lesson_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"))
    skill_id: Mapped[int | None] = mapped_column(ForeignKey("skills.id", ondelete="SET NULL"))
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("adaptive_plans.id", ondelete="SET NULL"))
    mode: Mapped[str] = mapped_column(String(16))  # lesson | practice | personalized | legendary
    status: Mapped[str] = mapped_column(String(16), default="active")  # active|completed|failed|abandoned
    queue: Mapped[list] = mapped_column(JSON)  # ordered exercise ids; grows when mistakes are re-queued
    answered: Mapped[int] = mapped_column(Integer, default=0)  # pointer into queue
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    mistake_count: Mapped[int] = mapped_column(Integer, default=0)
    hearts_lost: Mapped[int] = mapped_column(Integer, default=0)
    combo: Mapped[int] = mapped_column(Integer, default=0)
    best_combo: Mapped[int] = mapped_column(Integer, default=0)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    accuracy: Mapped[float | None] = mapped_column(Float)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    day: Mapped[date | None] = mapped_column(Date)  # learner-local day it was completed on


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"
    __table_args__ = (Index("ix_attempts_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("lesson_sessions.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"), index=True)
    answer: Mapped[dict] = mapped_column(JSON)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    is_typo: Mapped[bool] = mapped_column(Boolean, default=False)
    error_type: Mapped[str | None] = mapped_column(String(32))
    time_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class XpEvent(Base):
    __tablename__ = "xp_events"
    __table_args__ = (Index("ix_xp_user_day", "user_id", "day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    amount: Mapped[int]
    source: Mapped[str] = mapped_column(String(24))  # lesson | practice | personalized | chest | legendary
    day: Mapped[date] = mapped_column(Date)  # learner-local (simulated) day
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
