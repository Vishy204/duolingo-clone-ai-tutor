"""Read models over the learner's data, used by agent tools, the rule-based fallback, the voice
agent and the API. Plain functions (no LLM), so they are unit-testable and reusable."""
from collections import Counter
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import user_now
from app.models import (
    Concept,
    Exercise,
    ExerciseAttempt,
    LessonSession,
    Lexeme,
    User,
    UserConceptMastery,
)
from app.services import progress
from app.services.exercise_types import PRODUCTION_TYPES, display_answer
from app.services.mastery import mastery_level


def _ratio(c: int, n: int) -> float | None:
    return round(c / n, 2) if n else None


def concept_mastery(db: Session, user: User) -> list[dict]:
    now = user_now(user.clock_offset_days)
    rows = db.execute(
        select(UserConceptMastery, Concept)
        .join(Concept, Concept.id == UserConceptMastery.concept_id)
        .where(UserConceptMastery.user_id == user.id)
        .order_by(UserConceptMastery.mastery)
    ).all()
    return [
        {
            "concept_key": c.key,
            "name": c.name,
            "mastery": round(m.mastery, 2),
            "level": mastery_level(m.mastery),
            "attempts": m.attempts,
            "accuracy": _ratio(m.correct, m.attempts),
            "recognition_accuracy": _ratio(m.recognition_correct, m.recognition_attempts),
            "production_accuracy": _ratio(m.production_correct, m.production_attempts),
            "due_for_review": bool(m.next_review_at and m.next_review_at <= now),
        }
        for m, c in rows
    ]


def recent_mistakes(db: Session, user: User, limit: int = 20) -> list[dict]:
    rows = db.execute(
        select(ExerciseAttempt, Exercise)
        .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
        .where(
            ExerciseAttempt.user_id == user.id,
            (ExerciseAttempt.is_correct.is_(False)) | (ExerciseAttempt.is_typo.is_(True)),
        )
        .order_by(ExerciseAttempt.id.desc())
        .limit(limit)
    ).all()
    out = []
    for a, ex in rows:
        answer = a.answer or {}
        given = answer.get("text") or " ".join(answer.get("tokens") or []) or answer.get("choice")
        if isinstance(given, int) and ex.type == "multiple_choice":
            choices = ex.payload.get("choices", [])
            given = choices[given]["text"] if 0 <= given < len(choices) else None
        out.append({
            "attempt_id": a.id,
            "exercise_type": ex.type,
            "concepts": [c.key for c in ex.concepts],
            "task": ex.payload.get("source") or ex.payload.get("sentence") or ex.payload.get("question") or ex.prompt,
            "learner_answer": (
                given if given not in (None, "") else ("(simulated)" if answer.get("simulated") else None)
            ),
            "sample": bool(answer.get("simulated") or answer.get("simulated_profile")),
            "correct_answer": display_answer(ex.type, ex.payload),
            "error_type": a.error_type,
            "typo_only": a.is_typo and a.is_correct,
            "when": a.created_at.isoformat(timespec="minutes"),
        })
    return out


def error_breakdown(db: Session, user: User, window: int = 150) -> dict:
    rows = db.execute(
        select(ExerciseAttempt, Exercise)
        .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
        .where(ExerciseAttempt.user_id == user.id)
        .order_by(ExerciseAttempt.id.desc())
        .limit(window)
    ).all()
    by_error = Counter()
    by_concept_wrong = Counter()
    by_concept_total = Counter()
    by_type = {"recognition": [0, 0], "production": [0, 0]}
    for a, ex in rows:
        mode = "production" if ex.type in PRODUCTION_TYPES else "recognition"
        by_type[mode][1] += 1
        by_type[mode][0] += int(a.is_correct)
        if a.error_type:
            by_error[a.error_type] += 1
        for c in ex.concepts:
            by_concept_total[c.key] += 1
            if not a.is_correct:
                by_concept_wrong[c.key] += 1
    return {
        "attempts_analysed": len(rows),
        "errors_by_type": dict(by_error.most_common()),
        "error_rate_by_concept": {
            k: {"wrong": by_concept_wrong[k], "total": n, "rate": round(by_concept_wrong[k] / n, 2)}
            for k, n in by_concept_total.most_common()
        },
        "accuracy_recognition": _ratio(*by_type["recognition"]),
        "accuracy_production": _ratio(*by_type["production"]),
    }


def session_history(db: Session, user: User, limit: int = 8) -> list[dict]:
    rows = db.scalars(
        select(LessonSession)
        .where(LessonSession.user_id == user.id, LessonSession.status.in_(["completed", "failed"]))
        .order_by(LessonSession.id.desc())
        .limit(limit)
    ).all()
    return [
        {"mode": s.mode, "status": s.status, "accuracy": s.accuracy, "mistakes": s.mistake_count,
         "xp": s.xp_earned, "day": s.day.isoformat() if s.day else None}
        for s in rows
    ]


def concept_catalog(db: Session) -> list[dict]:
    return [{"key": c.key, "name": c.name, "category": c.category, "tip": c.tip}
            for c in db.scalars(select(Concept).order_by(Concept.id))]


def available_lesson_ids(db: Session, user: User, requested: list[str] | None = None) -> list[int]:
    """Lessons whose content the agents may draw on: everything studied, plus, when the learner
    explicitly asks for a topic, the course lessons that teach it (so "practise animals" works early)."""
    ids = set(progress.studied_lesson_ids(db, user))
    if requested:
        ids |= set(db.scalars(
            select(Exercise.lesson_id).join(Exercise.concepts)
            .where(Concept.key.in_(requested), Exercise.lesson_id.is_not(None))
        ).all())
    return list(ids)


def taught_lexicon(db: Session, user: User, concept_keys: list[str] | None = None, limit: int = 60,
                   requested: list[str] | None = None) -> list[dict]:
    """Vocabulary from lessons the learner has studied (the generator may only use these words)."""
    lesson_ids = available_lesson_ids(db, user, requested)
    q = select(Lexeme).where(Lexeme.lesson_id.in_(lesson_ids))
    words = db.scalars(q).all()
    if concept_keys:
        keys = set(concept_keys)
        words = sorted(words, key=lambda w: not any(c.key in keys for c in w.concepts))
    return [
        {"spanish": w.text, "english": w.translation, "emoji": w.emoji, "concepts": [c.key for c in w.concepts]}
        for w in words[:limit]
    ]


def taught_sentences(db: Session, user: User, concept_keys: list[str] | None = None, limit: int = 25,
                     requested: list[str] | None = None) -> list[dict]:
    lesson_ids = available_lesson_ids(db, user, requested)
    exercises = db.scalars(
        select(Exercise).where(Exercise.lesson_id.in_(lesson_ids), Exercise.type == "translate")
    ).all()
    keys = set(concept_keys or [])
    exercises = sorted(exercises, key=lambda e: not any(c.key in keys for c in e.concepts))
    out = []
    for e in exercises[:limit]:
        p = e.payload
        es = p["source"] if p["source_lang"] == "es" else p["answers"][0]
        en = p["answers"][0] if p["source_lang"] == "es" else p["source"]
        out.append({"spanish": es, "english": en, "concepts": [c.key for c in e.concepts]})
    return out


def taught_spanish_vocabulary(db: Session, user: User, requested: list[str] | None = None) -> set[str]:
    """Every Spanish token the learner has seen, for the generator's grounding check."""
    from app.services.grading import strip_accents, tokens

    vocab: set[str] = set()
    for w in taught_lexicon(db, user, limit=10_000, requested=requested):
        vocab.update(strip_accents(t) for t in tokens(w["spanish"]))
    for s in taught_sentences(db, user, limit=10_000, requested=requested):
        vocab.update(strip_accents(t) for t in tokens(s["spanish"]))
    return vocab


def recent_activity_since(db: Session, user: User, minutes: int) -> int:
    since = user_now(user.clock_offset_days) - timedelta(minutes=minutes)
    return len(db.scalars(
        select(ExerciseAttempt.id).where(ExerciseAttempt.user_id == user.id, ExerciseAttempt.created_at >= since)
    ).all())
