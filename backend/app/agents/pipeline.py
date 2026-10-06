"""Tutor orchestrator: analyse -> plan -> generate -> validate -> persist.

Code-orchestrated (not LLM-routed) on purpose: each step has a typed contract, so the sequence is
deterministic, debuggable and cheap, while each agent still reasons and calls tools on its own.

Triggered in the background after every lesson (never on the request path), on demand from the
Tutor Brain page, or by Smarto's `create_practice` tool. One run per learner at a time; a per-learner
daily budget caps cost; any failure degrades to the rule-based tutor.
"""
import asyncio
import json
import logging
import re
import time

from agents import (
    GuardrailFunctionOutput,
    OutputGuardrailTripwireTriggered,
    RunContextWrapper,
    output_guardrail,
    trace,
)
from sqlalchemy import select, update

from app.agents import fallback, learner_data
from app.agents.context import TutorContext
from app.agents.definitions import analyst_agent, generator_agent, planner_agent
from app.agents.observability import budget_left, finish_run, run_step, start_run
from app.agents.schemas import GeneratedSet, LearnerDiagnosis, PlanItem, PracticePlan
from app.agents.validation import Converted, validate_all
from app.core.clock import utcnow
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.text import strip_emoji
from app.models import AdaptivePlan, Concept, Exercise, User
from app.services.grading import normalize

log = logging.getLogger("tutor")

MIN_ATTEMPTS_FOR_AGENTS = 5
_locks: dict[int, asyncio.Lock] = {}


def _lock(user_id: int) -> asyncio.Lock:
    if len(_locks) > 10_000:
        _locks.clear()
    return _locks.setdefault(user_id, asyncio.Lock())


def is_running(user_id: int) -> bool:
    lock = _locks.get(user_id)
    return bool(lock and lock.locked())


ON_DEMAND_TRIGGERS = ("chat", "voice", "manual")


async def run_pipeline(user_id: int, trigger: str, focus_hint: list[str] | None = None,
                       session_factory=SessionLocal, force_rules: bool = False) -> int | None:
    lock = _lock(user_id)
    # Automatic triggers are idempotent: if a run is in flight, it already covers them. An explicit
    # request ("make me a practice on verbs") must never be dropped, so it waits its turn instead.
    if lock.locked() and trigger not in ON_DEMAND_TRIGGERS:
        log.info("pipeline already running for user %s; skipping (%s)", user_id, trigger)
        return None
    async with lock:
        with session_factory() as db:
            plan = AdaptivePlan(user_id=user_id, status="pending", trigger=trigger, engine="agents",
                                focus_concepts=focus_hint or [])
            db.add(plan)
            db.commit()
            plan_id = plan.id
            user = db.get(User, user_id)
            attempts = learner_data.error_breakdown(db, user)["attempts_analysed"]
            use_agents = (
                not force_rules and get_settings().agents_enabled and budget_left(db, user_id) > 0
                and attempts >= MIN_ATTEMPTS_FOR_AGENTS
            )
            reason = (
                "forced" if force_rules else "no OPENAI_API_KEY" if not get_settings().agents_enabled
                else "daily agent budget used" if budget_left(db, user_id) <= 0
                else "not enough data yet" if attempts < MIN_ATTEMPTS_FOR_AGENTS else None
            )
        if use_agents:
            try:
                await _run_agents(user_id, plan_id, trigger, focus_hint or [], session_factory)
                return plan_id
            except Exception as e:  # noqa: BLE001 - any failure degrades gracefully
                log.exception("agent pipeline failed for user %s", user_id)
                reason = f"agent pipeline failed: {type(e).__name__}"
        _run_rules(user_id, plan_id, trigger, focus_hint or [], session_factory, reason)
        return plan_id


# ---------------------------------------------------------------- agentic path

async def _run_agents(user_id: int, plan_id: int, trigger: str, focus_hint: list[str], session_factory) -> None:
    ctx = TutorContext(user_id=user_id, session_factory=session_factory, focus_hint=focus_hint)
    with session_factory() as db:
        user = db.get(User, user_id)
        catalog = learner_data.concept_catalog(db)
        known = {c["key"] for c in catalog}
        requested = [k for k in focus_hint if k in known]
        ctx.focus_hint = requested
        vocab = learner_data.taught_spanish_vocabulary(db, user, requested)
        emoji = {normalize(w["spanish"]): w["emoji"] for w in learner_data.taught_lexicon(db, user, limit=500)}
        due = [m["concept_key"] for m in learner_data.concept_mastery(db, user) if m["due_for_review"]][:3]

    t0 = time.perf_counter()
    with trace("Adaptive tutor pipeline", group_id=f"learner-{user_id}", metadata={"trigger": trigger}):
        root = start_run(user_id, "pipeline", "Tutor Orchestrator", f"trigger={trigger} focus={focus_hint}",
                         plan_id=plan_id, ctx_factory=session_factory)
        try:
            # 1) Diagnose ------------------------------------------------------------
            hint = f" The learner asked to focus on: {', '.join(focus_hint)}." if focus_hint else ""
            res, _ = await run_step(
                analyst_agent(), f"Diagnose this learner (trigger: {trigger}).{hint}", ctx,
                plan_id=plan_id, parent_id=root,
            )
            diagnosis: LearnerDiagnosis = res.final_output
            diagnosis.weak_concepts = [w for w in diagnosis.weak_concepts if w.concept_key in known][:4]
            _update_plan(session_factory, plan_id, diagnosis=diagnosis.model_dump())

            # 2) Plan ------------------------------------------------------------------
            planner_input = json.dumps({
                "diagnosis": diagnosis.model_dump(),
                "learner_requested_focus": focus_hint,
                "due_for_review": due,
                "concept_catalog": [{"key": c["key"], "name": c["name"]} for c in catalog],
            }, ensure_ascii=False)
            res, _ = await run_step(planner_agent(), planner_input, ctx, plan_id=plan_id, parent_id=root)
            plan: PracticePlan = _sanitize_plan(res.final_output, known, diagnosis, requested)
            if requested:  # say exactly what they asked for, not the planner's general diagnosis
                names = {c["key"]: c["name"] for c in catalog}
                plan.learner_message = f"Here's the practice you asked for: {', '.join(names[k] for k in requested)}."
            _update_plan(session_factory, plan_id, plan=plan.model_dump(),
                         focus_concepts=[i.concept_key for i in plan.items])

            # 3) Generate (+ validator guardrail, one repair round) --------------------
            converted, errors = await _generate(ctx, plan, known, vocab, emoji, plan_id, root)

            # 4) Persist ----------------------------------------------------------------
            exercise_ids = _persist(session_factory, user_id, plan_id, plan, converted, errors, diagnosis,
                                    requested)
            finish_run(root, status="ok", latency_ms=int((time.perf_counter() - t0) * 1000), output={
                "weak_concepts": [w.concept_key for w in diagnosis.weak_concepts],
                "planned": sum(i.exercise_count for i in plan.items),
                "generated_valid": len(converted), "rejected": errors, "exercise_ids": exercise_ids,
                "learner_message": plan.learner_message,
            }, ctx_factory=session_factory)
        except Exception as e:
            finish_run(root, status="error", error=f"{type(e).__name__}: {e}",
                       latency_ms=int((time.perf_counter() - t0) * 1000), ctx_factory=session_factory)
            raise


PRODUCTION = ["translate", "type_answer"]


def _sanitize_plan(plan: PracticePlan, known: set[str], diagnosis: LearnerDiagnosis,
                   requested: list[str] | None = None) -> PracticePlan:
    """Deterministic guard-rails on the planner's output (bounds + pedagogy invariants)."""
    modes = {w.concept_key: w.weakness_mode for w in diagnosis.weak_concepts}
    items = [i for i in plan.items if i.concept_key in known][:4]
    if requested:  # the learner asked for these topics: the session is about them, nothing else
        items = [i for i in items if i.concept_key in requested]
        for key in requested:
            if all(i.concept_key != key for i in items):
                items.append(PlanItem(
                    concept_key=key, exercise_count=max(2, 8 // len(requested)), difficulty=1,
                    exercise_types=["multiple_choice", "match_pairs", "translate", "type_answer"],
                    reason="You asked to practise this.",
                ))
        plan.review_concepts = []
    for i in items:
        i.exercise_count = max(1, min(4, i.exercise_count))
        i.difficulty = max(1, min(3, i.difficulty))
        i.exercise_types = i.exercise_types or ["multiple_choice", "translate"]
        # Invariant: a production weakness is trained mostly by producing (one warm-up allowed).
        if modes.get(i.concept_key) == "production":
            prod = [t for t in i.exercise_types if t in PRODUCTION] or PRODUCTION
            warmup = [t for t in i.exercise_types if t not in PRODUCTION][:1]
            i.exercise_types = list(dict.fromkeys(prod + warmup))
    total = sum(i.exercise_count for i in items)
    while total > 10 and items:  # trim the largest item until within budget
        big = max(items, key=lambda x: x.exercise_count)
        big.exercise_count -= 1
        total -= 1
    plan.items = items
    plan.review_concepts = [c for c in plan.review_concepts if c in known][:3]
    plan.learner_message = re.sub(r"^\s*Smarto\s*:\s*", "", strip_emoji(plan.learner_message))[:220]
    return plan


async def _generate(ctx: TutorContext, plan: PracticePlan, known, vocab, emoji, plan_id: int, root: int):
    state: dict = {}

    @output_guardrail
    async def exercises_are_valid(_: RunContextWrapper, __, output: GeneratedSet) -> GuardrailFunctionOutput:
        ok, errs = validate_all(output.exercises, known, vocab, emoji)
        state["ok"], state["errors"] = ok, errs
        too_many_bad = len(ok) < max(3, len(output.exercises) // 2)
        return GuardrailFunctionOutput(output_info={"valid": len(ok), "errors": errs}, tripwire_triggered=too_many_bad)

    request = json.dumps({"plan": [i.model_dump() for i in plan.items], "review_concepts": plan.review_concepts},
                         ensure_ascii=False)
    agent = generator_agent([exercises_are_valid])
    try:
        await run_step(agent, f"Write the exercises for this plan:\n{request}", ctx, plan_id=plan_id, parent_id=root)
        return state["ok"], state["errors"]
    except OutputGuardrailTripwireTriggered:
        first_errors = state.get("errors", [])
        repair = (
            f"Write the exercises for this plan:\n{request}\n\nYour previous attempt was rejected by the "
            f"validator. Fix these problems:\n- " + "\n- ".join(first_errors[:12])
        )
        try:
            await run_step(agent, repair, ctx, plan_id=plan_id, parent_id=root)
        except OutputGuardrailTripwireTriggered:
            pass  # keep whatever was valid; seeded exercises fill the gap
        return state.get("ok", []), first_errors + state.get("errors", [])


def _persist(session_factory, user_id: int, plan_id: int, plan: PracticePlan, converted: list[Converted],
             errors: list[str], diagnosis: LearnerDiagnosis, requested: list[str] | None = None) -> list[int]:
    with session_factory() as db:
        user = db.get(User, user_id)
        concepts = {c.key: c for c in db.scalars(select(Concept))}
        ids: list[int] = []
        for c in sorted(converted, key=lambda x: x.difficulty):
            ex = Exercise(
                lesson_id=None, type=c.type, prompt=c.prompt, payload=c.payload, difficulty=c.difficulty,
                source="agent", owner_user_id=user_id, plan_id=plan_id, rationale=c.rationale,
            )
            ex.concepts = [concepts[k] for k in c.concepts if k in concepts]
            db.add(ex)
            db.flush()
            ids.append(ex.id)
        target = max(6, min(10, sum(i.exercise_count for i in plan.items)))
        focus = [i.concept_key for i in plan.items] + plan.review_concepts
        production_focus = any(w.weakness_mode == "production" for w in diagnosis.weak_concepts[:2])
        ids += fallback.seeded_fill(db, user, focus, set(ids), target - len(ids),
                                    prefer_types=set(PRODUCTION) if production_focus else None,
                                    requested=requested)

        db.execute(
            update(AdaptivePlan)
            .where(AdaptivePlan.user_id == user_id, AdaptivePlan.status == "ready", AdaptivePlan.id != plan_id)
            .values(status="superseded")
        )
        p = db.get(AdaptivePlan, plan_id)
        p.plan = {**plan.model_dump(), "exercise_ids": ids, "generated_count": len(converted),
                  "seeded_count": len(ids) - len(converted), "validation_errors": errors[:20]}
        p.summary = plan.learner_message
        p.status = "ready" if ids else "failed"
        p.completed_at = utcnow()
        db.commit()
        return ids


def _update_plan(session_factory, plan_id: int, **fields) -> None:
    with session_factory() as db:
        p = db.get(AdaptivePlan, plan_id)
        for k, v in fields.items():
            setattr(p, k, v)
        db.commit()


# ---------------------------------------------------------------- rule-based path

def _run_rules(user_id: int, plan_id: int, trigger: str, focus_hint: list[str], session_factory,
               reason: str | None) -> None:
    t0 = time.perf_counter()
    run_id = start_run(user_id, "step", "Rules Engine", f"fallback: {reason}", plan_id=plan_id,
                       ctx_factory=session_factory)
    with session_factory() as db:
        user = db.get(User, user_id)
        diagnosis = fallback.diagnose(db, user)
        plan, ids, message = fallback.plan_and_pick(db, user, diagnosis, focus_hint)
        db.execute(
            update(AdaptivePlan)
            .where(AdaptivePlan.user_id == user_id, AdaptivePlan.status == "ready", AdaptivePlan.id != plan_id)
            .values(status="superseded")
        )
        p = db.get(AdaptivePlan, plan_id)
        p.engine = "rules"
        p.diagnosis = diagnosis
        p.plan = {**plan, "exercise_ids": ids, "generated_count": 0, "seeded_count": len(ids),
                  "fallback_reason": reason}
        p.focus_concepts = [i["concept_key"] for i in plan["items"]]
        p.summary = message
        p.status = "ready" if ids else "failed"
        p.error = reason
        p.completed_at = utcnow()
        db.commit()
    finish_run(run_id, status="fallback", output={"diagnosis": diagnosis, "plan": plan, "reason": reason},
               latency_ms=int((time.perf_counter() - t0) * 1000), model="rules", ctx_factory=session_factory)


_background: set[asyncio.Task] = set()


def schedule(user_id: int, trigger: str, focus_hint: list[str] | None = None) -> None:
    """Fire-and-forget from inside a running event loop (Smarto's tool, the voice agent)."""
    task = asyncio.get_running_loop().create_task(run_pipeline(user_id, trigger, focus_hint))
    _background.add(task)  # keep a reference so the task isn't garbage-collected mid-run
    task.add_done_callback(_background.discard)
