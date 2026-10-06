"""Duo: the conversational tutor (text chat) and the "Explain my mistake" agent.

Duo orchestrates other agents as tools (the Analyst via `.as_tool()`), can take actions
(create_practice schedules the adaptive pipeline), and sits behind an input guardrail that
blocks off-topic requests and prompt injection before the main model ever runs.
"""
import json

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    function_tool,
    input_guardrail,
    trace,
)
from sqlalchemy import select

from app.agents import learner_data, pipeline
from app.agents.context import TutorContext
from app.agents.definitions import DUO_INSTRUCTIONS, _settings, analyst_agent, explainer_agent, topic_guard_agent
from app.agents.observability import run_step
from app.agents.schemas import Explanation, TopicVerdict
from app.core.config import get_settings
from app.core.text import strip_emoji
from app.models import AdaptivePlan, Concept, Exercise, ExerciseAttempt, TutorMessage, User
from app.services.exercise_types import display_answer

HISTORY_TURNS = 8
BLOCKED_REPLY = "I'm your Spanish tutor, so let's stick to language learning. ¿Qué quieres aprender?"


@input_guardrail
async def topic_guard(ctx: RunContextWrapper[TutorContext], agent: Agent, input) -> GuardrailFunctionOutput:
    latest = input if isinstance(input, str) else next(
        (m.get("content") for m in reversed(input) if isinstance(m, dict) and m.get("role") == "user"), ""
    )
    result = await Runner.run(topic_guard_agent(), str(latest), context=ctx.context, max_turns=1)
    verdict: TopicVerdict = result.final_output
    return GuardrailFunctionOutput(output_info=verdict.model_dump(), tripwire_triggered=not verdict.allowed)


@function_tool
def explain_concept(ctx: RunContextWrapper[TutorContext], concept_key: str) -> str:
    """Get the course's official explanation of a grammar/vocabulary concept plus taught examples.

    Args:
        concept_key: e.g. grammar.gender_articles, verb.ser, spelling.accents
    """
    with ctx.context.session_factory() as db:
        c = db.scalar(select(Concept).where(Concept.key == concept_key))
        if c is None:
            keys = [k for k in db.scalars(select(Concept.key))]
            return json.dumps({"error": "unknown concept", "valid_keys": keys})
        user = db.get(User, ctx.context.user_id)
        return json.dumps({
            "name": c.name, "tip": c.tip,
            "examples": learner_data.taught_sentences(db, user, [concept_key], limit=4),
        }, ensure_ascii=False)


@function_tool
def get_learning_snapshot(ctx: RunContextWrapper[TutorContext]) -> str:
    """Instant snapshot of the learner: weakest concepts (with mastery), recent mistake types, streak/XP,
    and the latest diagnosis written by the Learner Analyst after their last lesson."""
    with ctx.context.session_factory() as db:
        user = db.get(User, ctx.context.user_id)
        plan = db.scalar(
            select(AdaptivePlan).where(AdaptivePlan.user_id == user.id, AdaptivePlan.diagnosis.is_not(None))
            .order_by(AdaptivePlan.id.desc()).limit(1)
        )
        weakest = [m for m in learner_data.concept_mastery(db, user) if m["attempts"] >= 2][:4]
        return json.dumps({
            "streak_days": user.streak_count, "total_xp": user.total_xp,
            "weakest_concepts": weakest,
            "errors_by_type": learner_data.error_breakdown(db, user, 80)["errors_by_type"],
            "latest_diagnosis": (plan.diagnosis or {}).get("overall_summary") if plan else None,
            "latest_plan_message": plan.summary if plan else None,
        }, ensure_ascii=False)


@function_tool
def create_practice(ctx: RunContextWrapper[TutorContext], concept_keys: list[str]) -> str:
    """Build a new personalized practice session focused on these concepts. It is generated in the
    background by the tutor pipeline and appears on the learner's path as "Duo's Practice".

    Args:
        concept_keys: concept keys to focus on, e.g. ["verb.ser"]
    """
    ctx.context.requested_practice = concept_keys
    pipeline.schedule(ctx.context.user_id, "chat", concept_keys)
    return json.dumps({"status": "building", "focus": concept_keys, "eta_seconds": 30})


def duo_agent() -> Agent[TutorContext]:
    analyst_tool = analyst_agent().as_tool(
        tool_name="analyze_my_learning",
        tool_description="Run the Learner Analyst on this learner's data: weak concepts, misconceptions, "
        "strengths. Use for questions about progress or what to study.",
        max_turns=6,
    )
    return Agent[TutorContext](
        name="Duo",
        instructions=DUO_INSTRUCTIONS,
        tools=[get_learning_snapshot, analyst_tool, explain_concept, create_practice],
        input_guardrails=[topic_guard],
        model=get_settings().openai_model,
        model_settings=_settings("low"),
    )


async def chat(db, user: User, message: str) -> dict:
    history = db.scalars(
        select(TutorMessage)
        .where(TutorMessage.user_id == user.id, TutorMessage.blocked.is_(False))
        .order_by(TutorMessage.id.desc())
        .limit(HISTORY_TURNS)
    ).all()[::-1]
    items = [{"role": m.role, "content": m.content} for m in history]
    items.append({"role": "user", "content": message})

    db.add(TutorMessage(user_id=user.id, role="user", content=message))
    db.commit()

    ctx = TutorContext(user_id=user.id)
    blocked = False
    with trace("Duo chat", group_id=f"learner-{user.id}"):
        try:
            result, _ = await run_step(duo_agent(), items, ctx, kind="chat", max_turns=6)
            reply = strip_emoji(str(result.final_output))
        except InputGuardrailTripwireTriggered:
            reply, blocked = BLOCKED_REPLY, True

    db.add(TutorMessage(user_id=user.id, role="assistant", content=reply, blocked=blocked))
    if blocked:  # don't keep the off-topic turn in Duo's memory either
        last_user = db.scalar(
            select(TutorMessage).where(TutorMessage.user_id == user.id, TutorMessage.role == "user")
            .order_by(TutorMessage.id.desc()).limit(1)
        )
        if last_user:
            last_user.blocked = True
    db.commit()
    return {"reply": reply, "blocked": blocked, "practice_requested": ctx.requested_practice}


async def explain_attempt(db, user: User, attempt_id: int) -> dict:
    attempt = db.get(ExerciseAttempt, attempt_id)
    if attempt is None or attempt.user_id != user.id:
        return {"error": "not_found"}
    ex = db.get(Exercise, attempt.exercise_id)
    answer = attempt.answer or {}
    given = answer.get("text") or " ".join(answer.get("tokens") or []) or answer.get("choice")
    if ex.type == "multiple_choice" and isinstance(given, int):
        given = ex.payload["choices"][given]["text"]
    payload = {
        "exercise_type": ex.type,
        "task": ex.payload.get("source") or ex.payload.get("sentence") or ex.payload.get("question"),
        "learner_answer": given,
        "correct_answer": display_answer(ex.type, ex.payload),
        "error_type": attempt.error_type,
        "concept_rules": [{"concept": c.name, "rule": c.tip} for c in ex.concepts],
    }
    ctx = TutorContext(user_id=user.id)
    with trace("Explain mistake", group_id=f"learner-{user.id}"):
        result, _ = await run_step(explainer_agent(), json.dumps(payload, ensure_ascii=False), ctx,
                                   kind="explain", max_turns=1)
    out: Explanation = result.final_output
    return {k: strip_emoji(v) if isinstance(v, str) else v for k, v in out.model_dump().items()}
