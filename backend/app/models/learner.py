"""Learner state: profile/gamification counters, per-skill progress, per-concept mastery, achievements."""
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utcnow
from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True)
    display_name: Mapped[str] = mapped_column(String(60))
    avatar_color: Mapped[str] = mapped_column(String(16), default="#1CB0F6")
    is_guest: Mapped[bool] = mapped_column(Boolean, default=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # seeded leaderboard learners
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    gems: Mapped[int] = mapped_column(Integer, default=500)
    hearts: Mapped[int] = mapped_column(Integer, default=5)
    hearts_updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    streak_count: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[date | None] = mapped_column(Date)
    streak_freezes: Mapped[int] = mapped_column(Integer, default=0)
    daily_goal_xp: Mapped[int] = mapped_column(Integer, default=20)
    clock_offset_days: Mapped[int] = mapped_column(Integer, default=0)  # demo "time travel"
    settings: Mapped[dict] = mapped_column(JSON, default=dict)

    skill_progress: Mapped[list["UserSkillProgress"]] = relationship(back_populates="user")


class UserSkillProgress(Base):
    __tablename__ = "user_skill_progress"
    __table_args__ = (UniqueConstraint("user_id", "skill_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    lessons_completed: Mapped[int] = mapped_column(Integer, default=0)
    crowns: Mapped[int] = mapped_column(Integer, default=0)
    is_legendary: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped[User] = relationship(back_populates="skill_progress")


class UserConceptMastery(Base):
    """Deterministic learner model, updated on every attempt (see services/mastery.py)."""

    __tablename__ = "user_concept_mastery"
    __table_args__ = (UniqueConstraint("user_id", "concept_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), index=True)
    mastery: Mapped[float] = mapped_column(Float, default=0.3)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    recognition_attempts: Mapped[int] = mapped_column(Integer, default=0)
    recognition_correct: Mapped[int] = mapped_column(Integer, default=0)
    production_attempts: Mapped[int] = mapped_column(Integer, default=0)
    production_correct: Mapped[int] = mapped_column(Integer, default=0)
    correct_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(48), unique=True)
    title: Mapped[str] = mapped_column(String(60))
    description: Mapped[str] = mapped_column(String(160))
    icon: Mapped[str] = mapped_column(String(16))
    color: Mapped[str] = mapped_column(String(16))
    metric: Mapped[str] = mapped_column(String(32))  # total_xp | streak | lessons | perfect | skills | personalized
    threshold: Mapped[int]


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id", ondelete="CASCADE"))
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    achievement: Mapped[Achievement] = relationship(lazy="joined")
