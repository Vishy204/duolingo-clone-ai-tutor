"""Course content: course -> unit -> skill -> lesson -> exercise, plus concepts and vocabulary."""
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utcnow
from app.core.db import Base

exercise_concepts = Table(
    "exercise_concepts",
    Base.metadata,
    Column("exercise_id", ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True),
    Column("concept_id", ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
)

lexeme_concepts = Table(
    "lexeme_concepts",
    Base.metadata,
    Column("lexeme_id", ForeignKey("lexemes.id", ondelete="CASCADE"), primary_key=True),
    Column("concept_id", ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(32), unique=True)
    title: Mapped[str] = mapped_column(String(80))
    from_lang: Mapped[str] = mapped_column(String(8))
    to_lang: Mapped[str] = mapped_column(String(8))
    flag: Mapped[str] = mapped_column(String(8))

    units: Mapped[list["Unit"]] = relationship(back_populates="course", order_by="Unit.position")


class Unit(Base):
    __tablename__ = "units"
    __table_args__ = (UniqueConstraint("course_id", "position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(255))
    color: Mapped[str] = mapped_column(String(16))
    guidebook: Mapped[list] = mapped_column(JSON, default=list)  # [{es, en}] key phrases

    course: Mapped[Course] = relationship(back_populates="units")
    skills: Mapped[list["Skill"]] = relationship(back_populates="unit", order_by="Skill.position")


class Skill(Base):
    """A node on the learning path. kind: lesson | chest | trophy."""

    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("unit_id", "position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    title: Mapped[str] = mapped_column(String(80))
    icon: Mapped[str] = mapped_column(String(16))
    kind: Mapped[str] = mapped_column(String(16), default="lesson")

    unit: Mapped[Unit] = relationship(back_populates="skills")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="skill", order_by="Lesson.position")


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("skill_id", "position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    title: Mapped[str] = mapped_column(String(80))

    skill: Mapped[Skill] = relationship(back_populates="lessons")
    exercises: Mapped[list["Exercise"]] = relationship(
        back_populates="lesson", order_by="Exercise.position", foreign_keys="Exercise.lesson_id"
    )


class Concept(Base):
    """A learnable unit of knowledge (a grammar rule, a vocab cluster, a spelling rule).

    Exercises are tagged with concepts; the learner model tracks mastery per concept and the
    tutor agents reason in terms of concepts.
    """

    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(16))  # vocab | grammar | spelling | verb
    tip: Mapped[str] = mapped_column(Text)


class Lexeme(Base):
    """Vocabulary taught by the course. Grounds the exercise-generator agent and voice Duo."""

    __tablename__ = "lexemes"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(String(80))  # target language, with article for nouns
    translation: Mapped[str] = mapped_column(String(80))
    emoji: Mapped[str | None] = mapped_column(String(16))

    concepts: Mapped[list[Concept]] = relationship(secondary=lexeme_concepts, lazy="selectin")


class Exercise(Base):
    """One exercise. `payload` holds the type-specific body (see app/services/exercise_types.py).

    source='seed' rows belong to a lesson; source='agent' rows are generated per learner by the
    tutor agents and are owned by that learner (owner_user_id) and the plan that produced them.
    """

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(default=0)
    type: Mapped[str] = mapped_column(String(24))
    prompt: Mapped[str] = mapped_column(String(255))
    payload: Mapped[dict] = mapped_column(JSON)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[str] = mapped_column(String(8), default="seed", index=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("adaptive_plans.id", ondelete="CASCADE"), index=True)
    rationale: Mapped[str | None] = mapped_column(Text)  # why the agent generated it
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    lesson: Mapped[Lesson | None] = relationship(back_populates="exercises", foreign_keys=[lesson_id])
    concepts: Mapped[list[Concept]] = relationship(secondary=exercise_concepts, lazy="selectin")
