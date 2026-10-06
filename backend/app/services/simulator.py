"""Reviewer tool: inject a burst of realistic mistakes for a chosen learner profile, so anyone can
check that the tutor genuinely adapts to *new* behaviour (not a canned demo).

Wrong answers are derived from the real correct answers (article swapped, accents dropped, words
shuffled, verb form changed...) and go through the same grader and learner model as live answers.
"""
import random
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import user_now
from app.models import Exercise, ExerciseAttempt, User
from app.services import mastery, progress
from app.services.exercise_types import PRODUCTION_TYPES, display_answer
from app.services.grading import grade, strip_accents

SWAP_ARTICLE = {"el": "la", "la": "el", "un": "una", "una": "un", "los": "las", "las": "los"}
SWAP_VERB = {"soy": "es", "es": "soy", "eres": "es", "como": "come", "come": "como", "comes": "come",
             "bebo": "bebe", "bebe": "bebo", "bebes": "bebe", "tengo": "tiene", "tiene": "tengo", "somos": "son"}

PROFILES = {
    "gender": {
        "label": "Mixes up el / la",
        "description": "Uses the wrong article: 'la pan', 'el manzana'.",
        "concepts": ["grammar.gender_articles"],
    },
    "accents": {
        "label": "Forgets accents",
        "description": "Types 'adios', 'nino', 'cafe' (accepted as typos, but a pattern).",
        "concepts": ["spelling.accents"],
    },
    "production": {
        "label": "Recognises but can't produce",
        "description": "Aces multiple choice, fails typing and translating.",
        "concepts": [],
    },
    "word_order": {
        "label": "Scrambles word order",
        "description": "Right words, wrong order in translations.",
        "concepts": [],
    },
    "verbs": {
        "label": "Confuses verb forms",
        "description": "'Yo es', 'Él soy': conjugates for the wrong person.",
        "concepts": ["verb.ser", "verb.comer_beber", "verb.tener"],
    },
}


def _swap(text: str, table: dict[str, str]) -> str | None:
    words = text.split()
    for i, w in enumerate(words):
        core = re.sub(r"[^\wáéíóúñ]", "", w.lower())
        if core in table:
            repl = table[core]
            words[i] = repl.capitalize() if w[:1].isupper() else repl
            return " ".join(words)
    return None


def _wrong_answer(profile: str, ex: Exercise, rng: random.Random) -> dict | None:
    p = ex.payload
    correct = display_answer(ex.type, p)
    if profile == "gender":
        if ex.type == "fill_blank":
            wrong = next((c for c in p["choices"] if c.lower() in SWAP_ARTICLE and c != p["answer"]), None)
            return {"choice": wrong} if wrong else None
        if ex.type in ("translate", "type_answer") and p["target_lang"] == "es":
            w = _swap(p["answers"][0], SWAP_ARTICLE)
            return {"text": w} if w else None
        return None
    if profile == "accents":
        if ex.type in PRODUCTION_TYPES and p["target_lang"] == "es":
            w = strip_accents(p["answers"][0])
            return {"text": w} if w != p["answers"][0] else None
        return None
    if profile == "production":
        if ex.type in PRODUCTION_TYPES:
            toks = correct.split()
            if len(toks) >= 2:
                toks = toks[:-1]  # drops a word
            return {"text": " ".join(toks)}
        if ex.type == "multiple_choice":
            return {"choice": p["answer"], "_correct": True}
        if ex.type == "fill_blank":
            return {"choice": p["answer"], "_correct": True}
        return None
    if profile == "word_order":
        if ex.type == "translate":
            toks = p["answers"][0].split()
            if len(toks) < 3:
                return None
            shuffled = toks[:]
            while shuffled == toks:
                rng.shuffle(shuffled)
            return {"tokens": shuffled}
        return None
    if profile == "verbs":
        if ex.type == "fill_blank" and p["answer"].lower() in SWAP_VERB:
            wrong = next((c for c in p["choices"] if c != p["answer"]), None)
            return {"choice": wrong}
        if ex.type in PRODUCTION_TYPES and p["target_lang"] == "es":
            w = _swap(p["answers"][0], SWAP_VERB)
            return {"text": w} if w else None
        return None
    return None


def inject(db: Session, user: User, profile: str, n: int = 14) -> dict:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile}")
    rng = random.Random()
    lesson_ids = progress.studied_lesson_ids(db, user)
    # Verb profiles need verb content; widen to the whole first unit if the learner is early on.
    pool = db.scalars(select(Exercise).where(Exercise.lesson_id.is_not(None))).all()
    studied = [e for e in pool if e.lesson_id in set(lesson_ids)]
    candidates = studied if profile != "verbs" else pool
    rng.shuffle(candidates)

    now = user_now(user.clock_offset_days)
    injected, examples = 0, []
    for ex in candidates:
        if injected >= n:
            break
        answer = _wrong_answer(profile, ex, rng)
        if answer is None:
            continue
        answer.pop("_correct", None)
        result = grade(ex.type, ex.payload, answer)
        db.add(ExerciseAttempt(
            user_id=user.id, exercise_id=ex.id, answer={**answer, "simulated_profile": profile},
            is_correct=result.correct, is_typo=result.typo, error_type=result.error_type,
            time_ms=rng.randint(3000, 9000), created_at=now,
        ))
        mastery.update_for_attempt(db, user, ex, result.correct, result.typo)
        injected += 1
        if len(examples) < 5 and (not result.correct or result.typo):
            given = answer.get("text") or " ".join(answer.get("tokens") or []) or answer.get("choice")
            examples.append({"answer": given, "correct": result.correct_answer, "error_type": result.error_type})
    db.flush()
    return {"profile": profile, "injected": injected, "examples": examples}
