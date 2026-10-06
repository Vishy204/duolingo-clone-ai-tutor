"""The lesson loop: build a session, grade answers one by one, finish and reward.

Modes
- lesson:        a path lesson. Mistakes cost a heart and the exercise comes back at the end.
                 Up to 2 of Smarto's personalized exercises (from the latest ready plan) are mixed in.
- practice:      "practice to earn hearts": targets the weakest / due-for-review concepts using
                 already-taught content. No hearts lost; finishing gives +1 heart.
- personalized:  the session built by the tutor agents (AdaptivePlan). Hearts are used.
- legendary:     timed, production-only challenge on a completed skill; 3 mistakes and you fail.
"""
import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import user_now, user_today
from app.core.config import get_settings
from app.models import AdaptivePlan, Concept, Exercise, ExerciseAttempt, LessonSession, User, UserConceptMastery
from app.models.content import exercise_concepts
from app.services import achievements, hearts, mastery, plans, progress, xp
from app.services.errors import GameError
from app.services.exercise_types import PRODUCTION_TYPES, public_payload, speakable_text
from app.services.grading import grade

HEART_MODES = {"lesson", "personalized"}


def _is_custom_session(db: Session, session: LessonSession) -> bool:
    """A practice the learner asked for (Custom Practice tab, chat, voice)."""
    if session.mode != "personalized" or not session.plan_id:
        return False
    plan = db.get(AdaptivePlan, session.plan_id)
    return plan is not None and plans.is_custom(plan)


def uses_hearts(db: Session, session: LessonSession) -> bool:
    # Practice the learner chose is like Duolingo's practice mode: it never costs hearts.
    return session.mode in HEART_MODES and not _is_custom_session(db, session)
MAX_REQUEUE = 2
LEGENDARY_MAX_MISTAKES = 3
XP_BY_MODE = {"lesson": 10, "practice": 10, "personalized": 15, "legendary": 40}


# ---------------------------------------------------------------- session creation

def start_session(
    db: Session, user: User, mode: str, lesson_id: int | None = None, skill_id: int | None = None,
    plan_id: int | None = None,
) -> LessonSession:
    hearts.regenerate(user)
    # Abandon any dangling active session so the learner only ever has one.
    for old in db.scalars(
        select(LessonSession).where(LessonSession.user_id == user.id, LessonSession.status == "active")
    ):
        old.status = "abandoned"
        old.ended_at = user_now(user.clock_offset_days)

    requested_plan, plan_id = plan_id, None
    if mode == "lesson":
        if lesson_id is None:
            raise GameError("bad_request", "lesson_id is required")
        lesson = progress.lesson_with_skill(db, lesson_id)
        if lesson is None:
            raise GameError("not_found", "Lesson not found", 404)
        _, states = progress.compute_path(db, user)
        state = states.get(lesson.skill_id)
        if state is None or state.status == "locked":
            raise GameError("locked", "Complete the previous levels to unlock this one.", 403)
        if user.hearts <= 0:
            raise GameError("no_hearts", "You ran out of hearts!", 409)
        exercises = list(lesson.exercises)
        extra = _duo_picks(db, user, limit=2)
        queue = [e.id for e in exercises]
        for i, e in enumerate(extra):  # sprinkle Smarto's picks into the middle of the lesson
            queue.insert(min(len(queue), 3 + i * 3), e.id)
        skill_id = lesson.skill_id
        plan_id = extra[0].plan_id if extra else None
    elif mode == "practice":
        queue = _practice_queue(db, user)
    elif mode == "personalized":
        if requested_plan is not None:  # a specific practice; finished ones can be replayed
            plan = db.get(AdaptivePlan, requested_plan)
            if plan is None or plan.user_id != user.id or plan.status not in ("ready", "consumed", "superseded"):
                raise GameError("no_plan", "That practice isn't ready yet.", 409)
        else:
            plan = plans.latest_ready_plan(db, user.id)
        if plan is None:
            raise GameError("no_plan", "Smarto is still preparing your personalized practice.", 409)
        if user.hearts <= 0 and not plans.is_custom(plan):
            raise GameError("no_hearts", "You ran out of hearts!", 409)
        queue = [e.id for e in plans.plan_exercises(db, plan)]
        plan_id = plan.id
    elif mode == "legendary":
        if skill_id is None:
            raise GameError("bad_request", "skill_id is required")
        _, states = progress.compute_path(db, user)
        state = states.get(skill_id)
        if state is None or state.lessons_completed < state.lessons_total or state.lessons_total == 0:
            raise GameError("locked", "Finish this level before going Legendary.", 403)
        pool = [e for lesson in state.skill.lessons for e in lesson.exercises]
        hard = [e for e in pool if e.type in PRODUCTION_TYPES]
        rng = random.Random()
        rng.shuffle(hard)
        queue = [e.id for e in hard[:10]]
    else:
        raise GameError("bad_request", f"Unknown mode {mode}")

    if not queue:
        raise GameError("empty", "Nothing to practice yet. Complete a lesson first!", 409)

    session = LessonSession(
        user_id=user.id, lesson_id=lesson_id, skill_id=skill_id, plan_id=plan_id, mode=mode,
        status="active", queue=queue, answered=0, correct_count=0, mistake_count=0, hearts_lost=0,
        combo=0, best_combo=0, xp_earned=0, started_at=user_now(user.clock_offset_days),
    )
    db.add(session)
    db.flush()
    return session


def _duo_picks(db: Session, user: User, limit: int) -> list[Exercise]:
    plan = plans.latest_ready_plan(db, user.id)
    if plan is None:
        return []
    return plans.unseen_plan_exercises(db, plan, user.id, limit)


def _practice_queue(db: Session, user: User, size: int = 10) -> list[int]:
    """Weakest concepts first, then concepts due for spaced review, from already-taught lessons."""
    lesson_ids = progress.studied_lesson_ids(db, user)
    if not lesson_ids:
        return []
    now = user_now(user.clock_offset_days)
    rows = db.execute(
        select(UserConceptMastery, Concept)
        .join(Concept, Concept.id == UserConceptMastery.concept_id)
        .where(UserConceptMastery.user_id == user.id)
    ).all()
    weak = sorted(rows, key=lambda r: r[0].mastery)
    due = [r for r in rows if r[0].next_review_at and r[0].next_review_at <= now]
    focus_ids = [r[1].id for r in weak[:3]] + [r[1].id for r in due]

    pool = db.scalars(select(Exercise).where(Exercise.lesson_id.in_(lesson_ids))).all()
    rng = random.Random()
    targeted = [e for e in pool if any(c.id in focus_ids for c in e.concepts)]
    rng.shuffle(targeted)
    # If production is the weak side, favour typing/translation exercises.
    prod_weak = any(
        r[0].production_attempts >= 2 and r[0].production_correct / r[0].production_attempts < 0.6 for r in weak[:3]
    )
    if prod_weak:
        targeted.sort(key=lambda e: e.type not in PRODUCTION_TYPES)
    chosen = targeted[:size]
    if len(chosen) < size:
        rest = [e for e in pool if e not in chosen]
        rng.shuffle(rest)
        chosen += rest[: size - len(chosen)]

    plan = plans.latest_ready_plan(db, user.id)
    if plan is not None:  # top up with Smarto's generated items
        chosen = plans.unseen_plan_exercises(db, plan, user.id, 3) + chosen[: size - 3]
    rng.shuffle(chosen)
    return [e.id for e in chosen]


# ---------------------------------------------------------------- serialization

def exercise_view(ex: Exercise, personalized: bool = False) -> dict:
    return {
        "id": ex.id,
        "type": ex.type,
        "prompt": ex.prompt,
        "data": public_payload(ex.type, ex.payload, rng_seed=ex.id),
        "concepts": [c.key for c in ex.concepts],
        "difficulty": ex.difficulty,
        "personalized": personalized or ex.source == "agent",
        "speak": speakable_text(ex.type, ex.payload),
    }


def session_view(db: Session, session: LessonSession, user: User) -> dict:
    ids = list(dict.fromkeys(session.queue))
    by_id = {e.id: e for e in db.scalars(select(Exercise).where(Exercise.id.in_(ids))).all()}
    return {
        "id": session.id,
        "mode": session.mode,
        "lesson_id": session.lesson_id,
        "skill_id": session.skill_id,
        "status": session.status,
        "exercises": [exercise_view(by_id[i]) for i in session.queue if i in by_id],
        "answered": session.answered,
        "hearts": user.hearts,
        "uses_hearts": uses_hearts(db, session),
        "custom": _is_custom_session(db, session),
        "max_mistakes": LEGENDARY_MAX_MISTAKES if session.mode == "legendary" else None,
        "time_limit_seconds": 150 if session.mode == "legendary" else None,
    }


# ---------------------------------------------------------------- answering

def get_owned_session(db: Session, user: User, session_id: int) -> LessonSession:
    session = db.get(LessonSession, session_id)
    if session is None or session.user_id != user.id:  # never leak other learners' sessions
        raise GameError("not_found", "Session not found", 404)
    return session


def submit_answer(
    db: Session, user: User, session: LessonSession, exercise_id: int, answer: dict, time_ms: int | None
) -> dict:
    if session.status != "active":
        raise GameError("inactive", "This lesson is already over.", 409)
    if session.answered >= len(session.queue):
        raise GameError("finished", "No exercises left. Finish the lesson.", 409)
    if session.queue[session.answered] != exercise_id:
        raise GameError("out_of_order", "That isn't the current exercise.", 409)

    hearts.regenerate(user)
    hearts_on = uses_hearts(db, session)
    if hearts_on and user.hearts <= 0:
        raise GameError("no_hearts", "You ran out of hearts!", 409)

    ex = db.get(Exercise, exercise_id)
    if ex is None or (ex.owner_user_id is not None and ex.owner_user_id != user.id):
        raise GameError("not_found", "Exercise not found", 404)

    result = grade(ex.type, ex.payload, answer)
    attempt = ExerciseAttempt(
        session_id=session.id, user_id=user.id, exercise_id=ex.id, answer=answer,
        is_correct=result.correct, is_typo=result.typo, error_type=result.error_type,
        time_ms=time_ms, created_at=user_now(user.clock_offset_days),
    )
    db.add(attempt)
    mastery.update_for_attempt(db, user, ex, result.correct, result.typo)

    # Match-pairs mistakes are part of the game itself: logged for the tutor, never punished.
    counts_as_correct = result.correct or (ex.type == "match_pairs" and not answer.get("skipped"))
    requeued = False
    failed = False
    if counts_as_correct:
        session.correct_count += 1
        session.combo += 1
        session.best_combo = max(session.best_combo, session.combo)
    else:
        session.mistake_count += 1
        session.combo = 0
        if hearts_on:
            hearts.lose_heart(user)
            session.hearts_lost += 1
        if session.mode == "legendary":
            failed = session.mistake_count >= LEGENDARY_MAX_MISTAKES
        elif session.queue.count(ex.id) < MAX_REQUEUE:
            session.queue = [*session.queue, ex.id]  # reassign so SQLAlchemy sees the JSON change
            requeued = True
    session.answered += 1
    if failed:
        session.status = "failed"
        session.ended_at = user_now(user.clock_offset_days)
    db.flush()

    return {
        "attempt_id": attempt.id,
        "correct": counts_as_correct,
        "typo": result.typo,
        "error_type": result.error_type,
        "feedback": result.feedback,
        "correct_answer": result.correct_answer,
        "requeued": requeued,
        "hearts": user.hearts,
        "out_of_hearts": hearts_on and user.hearts <= 0,
        "failed": failed,
        "combo": session.combo,
        "remaining": len(session.queue) - session.answered,
        "progress": session.correct_count / max(1, len(set(session.queue))),
    }


# ---------------------------------------------------------------- finishing

def complete_session(db: Session, user: User, session: LessonSession) -> dict:
    if session.status != "active":
        raise GameError("inactive", "This lesson is already over.", 409)
    if session.answered < len(session.queue):
        raise GameError("unfinished", "Finish all exercises first.", 409)

    s = get_settings()
    now = user_now(user.clock_offset_days)
    session.status = "completed"
    session.ended_at = now
    session.day = user_today(user.clock_offset_days)
    session.accuracy = round(session.correct_count / max(1, session.answered), 3)

    amount = XP_BY_MODE.get(session.mode, s.xp_per_lesson)
    if session.mode == "lesson" and session.mistake_count == 0:
        amount += s.xp_perfect_bonus
    session.xp_earned = amount
    streak_extended = xp.award(db, user, amount, session.mode)

    skill_completed = False
    if session.mode == "lesson" and session.skill_id:
        skill_completed = _advance_skill(db, user, session)
    elif session.mode == "legendary" and session.skill_id:
        p = _skill_progress(db, user.id, session.skill_id)
        p.is_legendary = True
    elif session.mode == "practice":
        hearts.gain_heart(user)
    elif session.mode == "personalized" and session.plan_id:
        plan = db.get(AdaptivePlan, session.plan_id)
        if plan and plan.status == "ready":
            plan.status = "consumed"
            plan.consumed_at = now
    db.flush()
    unlocked = achievements.check_and_unlock(db, user)
    db.flush()

    duration = int((now - session.started_at).total_seconds())
    return {
        "session_id": session.id,
        "mode": session.mode,
        "xp_earned": amount,
        "accuracy": session.accuracy,
        "mistakes": session.mistake_count,
        "best_combo": session.best_combo,
        "duration_seconds": max(duration, 1),
        "streak": user.streak_count,
        "streak_extended": streak_extended,
        "skill_completed": skill_completed,
        "hearts": user.hearts,
        "total_xp": user.total_xp,
        "xp_today": xp.xp_today(db, user),
        "daily_goal_xp": user.daily_goal_xp,
        "achievements": [
            {"key": a.key, "title": a.title, "color": a.color, "description": a.description}
            for a in unlocked
        ],
    }


def _skill_progress(db: Session, user_id: int, skill_id: int):
    from app.models import UserSkillProgress

    p = db.scalar(
        select(UserSkillProgress).where(UserSkillProgress.user_id == user_id, UserSkillProgress.skill_id == skill_id)
    )
    if p is None:
        p = UserSkillProgress(user_id=user_id, skill_id=skill_id, lessons_completed=0, crowns=0, is_legendary=False)
        db.add(p)
        db.flush()
    return p


def _advance_skill(db: Session, user: User, session: LessonSession) -> bool:
    lesson = progress.lesson_with_skill(db, session.lesson_id) if session.lesson_id else None
    if lesson is None:
        return False
    total = len(lesson.skill.lessons)
    p = _skill_progress(db, user.id, lesson.skill_id)
    # Only the next unplayed lesson moves the ring forward; replays just earn XP.
    if p.lessons_completed < total and lesson.position == p.lessons_completed + 1:
        p.lessons_completed += 1
        if p.lessons_completed >= total:
            p.crowns = max(p.crowns, 1)
            p.completed_at = user_now(user.clock_offset_days)
            return True
    return False


def concept_ids_for_exercises(db: Session, exercise_ids: list[int]) -> list[int]:
    return list(
        db.scalars(
            select(exercise_concepts.c.concept_id).where(exercise_concepts.c.exercise_id.in_(exercise_ids)).distinct()
        )
    )
