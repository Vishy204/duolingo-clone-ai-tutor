"""Guest learners. Auth is simplified per the brief: each visitor gets their own learner,
pre-loaded with realistic demo progress (so the path, streak and the tutor have something to
work with immediately), identified by a signed JWT.

The demo history deliberately contains a pattern, mostly el/la gender mistakes and a few missing
accents, so the tutor agents have a clear signal to diagnose and adapt to on the first visit.
"""
import random
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.models import Course, Exercise, ExerciseAttempt, LessonSession, Skill, Unit, User, UserSkillProgress, XpEvent
from app.services import achievements, mastery, simulator
from app.services.exercise_types import PRODUCTION_TYPES

ADJECTIVES = ["Happy", "Brave", "Swift", "Clever", "Sunny", "Jolly", "Mighty", "Calm"]
ANIMALS = ["Owl", "Fox", "Panda", "Koala", "Otter", "Tiger", "Llama", "Lynx"]
COLORS = ["#1CB0F6", "#FF9600", "#CE82FF", "#FF4B4B", "#2B70C9", "#00CD9C"]

# skill position in unit 1 -> lessons completed
DEMO_PROGRESS = {1: 2, 2: 3, 3: 1}


def create_guest(db: Session, name: str | None = None) -> User:
    course = db.scalar(select(Course).limit(1))
    rng = random.Random()
    display = name or f"{rng.choice(ADJECTIVES)} {rng.choice(ANIMALS)}"
    now = utcnow()
    today = now.date()
    user = User(
        username=f"guest_{secrets.token_hex(5)}",
        display_name=display[:60],
        avatar_color=rng.choice(COLORS),
        is_guest=True,
        course_id=course.id,
        total_xp=0,
        gems=500,
        hearts=5,
        hearts_updated_at=now,
        streak_count=3,
        longest_streak=3,
        last_active_date=today - timedelta(days=1),  # so finishing a lesson today extends the streak
        streak_freezes=1,
        daily_goal_xp=20,
        clock_offset_days=0,
        settings={"sound": True, "dark_mode": False, "voice": "duo"},
    )
    db.add(user)
    db.flush()
    # Fixed seed: every demo learner gets the same mistake pattern, so the first diagnosis is consistent.
    _seed_history(db, user, course, random.Random(2024))
    achievements.check_and_unlock(db, user)
    db.flush()
    return user


def _seed_history(db: Session, user: User, course: Course, rng: random.Random) -> None:
    unit1 = db.scalar(select(Unit).where(Unit.course_id == course.id, Unit.position == 1))
    skills = {s.position: s for s in db.scalars(select(Skill).where(Skill.unit_id == unit1.id))}
    now = utcnow()
    day_offsets = [3, 3, 2, 2, 1, 1]  # completed lessons spread over the last 3 days (streak of 3)
    session_i = 0

    for pos, done in DEMO_PROGRESS.items():
        skill = skills[pos]
        db.add(UserSkillProgress(
            user_id=user.id, skill_id=skill.id, lessons_completed=done,
            crowns=1 if done >= len(skill.lessons) else 0, is_legendary=False,
            completed_at=now - timedelta(days=1) if done >= len(skill.lessons) else None,
        ))
        for lesson in skill.lessons[:done]:
            days_ago = day_offsets[min(session_i, len(day_offsets) - 1)]
            session_i += 1
            when = now - timedelta(days=days_ago, hours=rng.randint(1, 5))
            exercises = db.scalars(select(Exercise).where(Exercise.lesson_id == lesson.id)).all()
            mistakes = 0
            for ex in exercises:
                correct, typo, err = _simulate_answer(ex, rng)
                mistakes += int(not correct)
                answer = {"simulated": True}
                if err in ("gender_article", "accent"):  # a realistic wrong answer reviewers can read
                    wrong = simulator._wrong_answer("gender" if err == "gender_article" else "accents", ex, rng)
                    if wrong:
                        answer = {**wrong, "simulated": True}
                db.add(ExerciseAttempt(
                    user_id=user.id, exercise_id=ex.id, answer=answer, is_correct=correct,
                    is_typo=typo, error_type=err, time_ms=rng.randint(2500, 9000), created_at=when,
                ))
                for concept in ex.concepts:
                    row = mastery._get_or_create(db, user.id, concept.id)
                    mastery.update_row(row, correct=correct, typo=typo,
                                       production=ex.type in PRODUCTION_TYPES, now=when)
            xp_amount = 10 + (5 if mistakes == 0 else 0)
            db.add(LessonSession(
                user_id=user.id, lesson_id=lesson.id, skill_id=skill.id, mode="lesson", status="completed",
                queue=[e.id for e in exercises], answered=len(exercises), correct_count=len(exercises) - mistakes,
                mistake_count=mistakes, hearts_lost=mistakes, combo=0, best_combo=len(exercises) - mistakes,
                xp_earned=xp_amount, accuracy=round(1 - mistakes / max(1, len(exercises)), 3),
                started_at=when - timedelta(minutes=4), ended_at=when, day=when.date(),
            ))
            db.add(XpEvent(user_id=user.id, amount=xp_amount, source="lesson", day=when.date(), created_at=when))
            user.total_xp += xp_amount
    db.flush()


def _simulate_answer(ex: Exercise, rng: random.Random) -> tuple[bool, bool, str | None]:
    keys = {c.key for c in ex.concepts}
    if "grammar.gender_articles" in keys and ex.type in ("fill_blank", "translate", "type_answer"):
        if rng.random() < 0.55:
            return False, False, "gender_article"
    if "spelling.accents" in keys and ex.type in PRODUCTION_TYPES and rng.random() < 0.5:
        return True, True, "accent"
    if rng.random() < 0.06:
        return False, False, "vocabulary"
    return True, False, None
