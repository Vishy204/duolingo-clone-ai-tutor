"""Rule-based tutor: same inputs and outputs as the agent pipeline, zero LLM calls.

Used when no API key is configured, the learner's daily agent budget is spent, or the agent
pipeline fails. The app keeps adapting either way; the agents just do it with more insight.
"""
import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import learner_data
from app.models import Concept, Exercise, User
from app.services import progress
from app.services.exercise_types import PRODUCTION_TYPES, RECOGNITION_TYPES

FRIENDLY = {
    "grammar.gender_articles": "el/la and un/una",
    "spelling.accents": "accents",
    "verb.comer_beber": "verb endings",
    "verb.ser": "the verb ser",
    "verb.tener": "the verb tener",
    "grammar.adjective_agreement": "adjective endings",
    "grammar.plurals": "plurals",
    "grammar.word_order": "questions and negation",
    "grammar.subject_pronouns": "pronouns",
}


def diagnose(db: Session, user: User) -> dict:
    mastery = learner_data.concept_mastery(db, user)
    breakdown = learner_data.error_breakdown(db, user)
    weak = []
    for m in mastery:
        if m["attempts"] < 2 or m["mastery"] >= 0.65:
            continue
        rec, prod = m["recognition_accuracy"], m["production_accuracy"]
        if rec is not None and prod is not None and prod + 0.15 < rec:
            mode = "production"
        elif rec is not None and prod is not None and rec + 0.15 < prod:
            mode = "recognition"
        else:
            mode = "both"
        weak.append({
            "concept_key": m["concept_key"],
            "severity": "high" if m["mastery"] < 0.35 else "medium" if m["mastery"] < 0.5 else "low",
            "weakness_mode": mode,
            "evidence": f"mastery {m['mastery']:.2f} over {m['attempts']} attempts, accuracy {m['accuracy']}",
            "likely_misconception": "",
        })
    return {
        "weak_concepts": weak[:3],
        "strengths": [m["concept_key"] for m in mastery if m["mastery"] >= 0.8][:5],
        "error_patterns": [f"{k}: {v}" for k, v in list(breakdown["errors_by_type"].items())[:4]],
        "overall_summary": "Rule-based diagnosis from mastery scores and error counts.",
        "confidence": min(1.0, breakdown["attempts_analysed"] / 60),
    }


def plan_and_pick(db: Session, user: User, diagnosis: dict, focus_hint: list[str] | None = None,
                  size: int = 8) -> tuple[dict, list[int], str]:
    weak = diagnosis["weak_concepts"]
    focus = list(dict.fromkeys((focus_hint or []) + [w["concept_key"] for w in weak]))[:2]
    if not focus:
        focus = [m["concept_key"] for m in learner_data.concept_mastery(db, user)[:2]]
    modes = {w["concept_key"]: w["weakness_mode"] for w in weak}

    lesson_ids = progress.studied_lesson_ids(db, user)
    concept_ids = {c.id: c.key for c in db.scalars(select(Concept).where(Concept.key.in_(focus)))}
    pool = db.scalars(select(Exercise).where(Exercise.lesson_id.in_(lesson_ids))).all()
    targeted = [e for e in pool if any(c.id in concept_ids for c in e.concepts)]
    rng = random.Random()
    rng.shuffle(targeted)

    def wanted(e: Exercise) -> int:
        mode = next((modes.get(c.key) for c in e.concepts if c.key in modes), "both")
        if mode == "production":
            return 0 if e.type in PRODUCTION_TYPES else 1
        if mode == "recognition":
            return 0 if e.type in RECOGNITION_TYPES else 1
        return 0

    targeted.sort(key=wanted)
    chosen = targeted[:size]
    chosen.sort(key=lambda e: e.difficulty)
    names = " and ".join(FRIENDLY.get(k, k.split(".")[-1].replace("_", " ")) for k in focus)
    message = f"I noticed {names} trip you up, so I picked {len(chosen)} exercises to strengthen them!"
    plan = {
        "items": [
            {"concept_key": k, "exercise_count": sum(1 for e in chosen if any(c.key == k for c in e.concepts)),
             "exercise_types": sorted({e.type for e in chosen}), "difficulty": 2,
             "reason": f"Lowest mastery ({modes.get(k, 'both')} weakness)"}
            for k in focus
        ],
        "review_concepts": [],
        "strategy": "Rule-based: weakest concepts first, formats matched to recognition vs production gaps.",
        "learner_message": message,
    }
    return plan, [e.id for e in chosen], message


def seeded_fill(db: Session, user: User, concept_keys: list[str], exclude: set[int], n: int,
                prefer_types: set[str] | None = None) -> list[int]:
    """Seeded exercises for the given concepts (used to top up an agent plan)."""
    if n <= 0:
        return []
    lesson_ids = progress.studied_lesson_ids(db, user)
    pool = db.scalars(select(Exercise).where(Exercise.lesson_id.in_(lesson_ids))).all()
    keys = set(concept_keys)
    targeted = [e for e in pool if e.id not in exclude and any(c.key in keys for c in e.concepts)]
    random.shuffle(targeted)
    if prefer_types:
        targeted.sort(key=lambda e: e.type not in prefer_types)
    return [e.id for e in targeted[:n]]
