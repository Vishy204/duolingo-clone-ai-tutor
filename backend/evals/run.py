"""Behavioural evals for the tutor agents (real LLM calls; needs OPENAI_API_KEY).

For each synthetic learner profile we start from a clean learner, inject a burst of that
profile's mistakes, run the full agent pipeline, and check the agents noticed the right thing and
adapted the practice to it.

    cd backend && python -m evals.run            # all profiles, in parallel
    python -m evals.run gender accents           # a subset
"""
import asyncio
import json
import os
import sys
import time

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/evals.db")

from agents import set_default_openai_key  # noqa: E402
from sqlalchemy import delete  # noqa: E402

from app.agents.pipeline import run_pipeline  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.db import SessionLocal  # noqa: E402
from app.models import AdaptivePlan, Exercise, ExerciseAttempt, UserConceptMastery  # noqa: E402
from app.seed.seed import run as seed  # noqa: E402
from app.services import guests, simulator  # noqa: E402

PRODUCTION = {"translate", "type_answer"}


def check(profile: str, plan: AdaptivePlan, exercises: list[Exercise]) -> list[tuple[str, bool]]:
    d = plan.diagnosis or {}
    weak = [w["concept_key"] for w in d.get("weak_concepts", [])]
    focus = [i["concept_key"] for i in (plan.plan or {}).get("items", [])]
    text = json.dumps(d).lower()
    types = [e.type for e in exercises]
    tagged = lambda key: sum(1 for e in exercises if key in [c.key for c in e.concepts])  # noqa: E731
    checks = [("ran on agents (not fallback)", plan.engine == "agents"), ("plan is ready", plan.status == "ready"),
              ("at least 6 exercises", len(exercises) >= 6)]
    if profile == "gender":
        checks += [("diagnoses gender/articles first", weak[:1] == ["grammar.gender_articles"]),
                   ("plan focuses on gender", "grammar.gender_articles" in focus[:2]),
                   ("most exercises drill gender", tagged("grammar.gender_articles") >= len(exercises) // 2)]
    elif profile == "accents":
        checks += [("diagnoses accents", "spelling.accents" in weak[:2]),
                   ("plan includes accent practice", "spelling.accents" in focus),
                   ("uses typing to practise accents", any(t in PRODUCTION for t in types))]
    elif profile == "production":
        checks += [("spots production weakness", "production" in text),
                   ("majority production exercises", sum(t in PRODUCTION for t in types) >= len(types) // 2)]
    elif profile == "word_order":
        checks += [("mentions word order", "order" in text),
                   ("uses sentence building", "translate" in types)]
    elif profile == "verbs":
        checks += [("diagnoses a verb concept", any(w.startswith("verb.") for w in weak[:2])),
                   ("plan focuses on verbs", any(f.startswith("verb.") for f in focus))]
    return checks


async def eval_profile(profile: str) -> tuple[str, list, float]:
    with SessionLocal() as db:
        user = guests.create_guest(db, f"eval-{profile}")
        # Start from a clean slate so the only signal is the injected profile.
        db.execute(delete(ExerciseAttempt).where(ExerciseAttempt.user_id == user.id))
        db.execute(delete(UserConceptMastery).where(UserConceptMastery.user_id == user.id))
        for _ in range(2):
            simulator.inject(db, user, profile, n=14)
        db.commit()
        uid = user.id
    t0 = time.perf_counter()
    plan_id = await run_pipeline(uid, f"eval:{profile}")
    secs = time.perf_counter() - t0
    with SessionLocal() as db:
        plan = db.get(AdaptivePlan, plan_id)
        ids = (plan.plan or {}).get("exercise_ids", [])
        exercises = db.query(Exercise).filter(Exercise.id.in_(ids)).all()
        return profile, check(profile, plan, exercises), secs


async def main(profiles: list[str]) -> int:
    seed()
    set_default_openai_key(get_settings().openai_api_key)
    results = await asyncio.gather(*(eval_profile(p) for p in profiles))
    failed = 0
    for profile, checks, secs in results:
        print(f"\n[{profile}]  ({secs:.1f}s)")
        for name, ok in checks:
            failed += not ok
            print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    total = sum(len(c) for _, c, _ in results)
    print(f"\n{total - failed}/{total} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    if not get_settings().openai_api_key:
        sys.exit("OPENAI_API_KEY is required for evals")
    chosen = sys.argv[1:] or list(simulator.PROFILES)
    sys.exit(asyncio.run(main(chosen)))
