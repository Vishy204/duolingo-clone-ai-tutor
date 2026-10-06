"""The agentic tutor's API: insights, the Tutor Brain timeline, chat, explanations, re-planning and
the reviewer simulator."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import duo, learner_data, pipeline
from app.agents.fallback import FRIENDLY
from app.agents.observability import budget_left
from app.api.deps import current_user
from app.core.config import get_settings
from app.core.db import get_db
from app.core.rate_limit import tutor_limiter
from app.models import AdaptivePlan, AgentRun, Exercise, TutorMessage, User
from app.schemas.api import ChatIn, ExplainIn, PlanIn, SimulateIn
from app.services import plans, simulator
from app.services.exercise_types import display_answer, public_payload

router = APIRouter(prefix="/tutor")


def _guard_agent_call(db: Session, user: User) -> None:
    tutor_limiter.check(f"u{user.id}")
    if not get_settings().agents_enabled:
        raise HTTPException(503, "The AI tutor isn't configured on this server.")
    if budget_left(db, user.id) <= 0:
        raise HTTPException(429, "Duo needs a rest! You've used today's tutor budget. Back tomorrow 🦉")


@router.get("/insights")
def insights(user: User = Depends(current_user), db: Session = Depends(get_db)):
    plan = plans.latest_plan(db, user.id)
    ready = plans.latest_ready_plan(db, user.id)
    mastery = learner_data.concept_mastery(db, user)
    weakest = [m for m in mastery if m["attempts"] >= 2][:3]
    return {
        "agents_enabled": get_settings().agents_enabled,
        "running": pipeline.is_running(user.id) or (plan is not None and plan.status == "pending"),
        "latest_plan": _plan_view(db, plan, with_exercises=False) if plan else None,
        "ready_plan": _plan_view(db, ready, with_exercises=False) if ready else None,
        "weakest": [{**m, "friendly": FRIENDLY.get(m["concept_key"], m["name"])} for m in weakest],
        "budget_left": budget_left(db, user.id),
    }


@router.get("/brain")
def brain(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Everything the evaluators need to see the agents at work, newest first."""
    plan_rows = db.scalars(
        select(AdaptivePlan).where(AdaptivePlan.user_id == user.id).order_by(AdaptivePlan.id.desc()).limit(8)
    ).all()
    runs = db.scalars(
        select(AgentRun).where(AgentRun.user_id == user.id).order_by(AgentRun.id.desc()).limit(80)
    ).all()
    runs_by_plan: dict[int | None, list] = {}
    for r in runs:
        runs_by_plan.setdefault(r.plan_id, []).append(_run_view(r))
    return {
        "agents_enabled": get_settings().agents_enabled,
        "model": get_settings().openai_model,
        "running": pipeline.is_running(user.id),
        "budget_left": budget_left(db, user.id),
        "mastery": learner_data.concept_mastery(db, user),
        "error_breakdown": learner_data.error_breakdown(db, user),
        "recent_mistakes": learner_data.recent_mistakes(db, user, 12),
        "plans": [{**_plan_view(db, p, with_exercises=True), "runs": sorted(runs_by_plan.get(p.id, []),
                                                                         key=lambda r: r["id"])}
                  for p in plan_rows],
        "other_runs": [r for r in runs_by_plan.get(None, [])][:20],
        "profiles": [{"key": k, **v} for k, v in simulator.PROFILES.items()],
    }


def _run_view(r: AgentRun) -> dict:
    return {
        "id": r.id, "parent_id": r.parent_id, "kind": r.kind, "agent": r.agent_name, "status": r.status,
        "input": r.input_summary, "output": r.output, "tool_calls": r.tool_calls, "model": r.model,
        "input_tokens": r.input_tokens, "output_tokens": r.output_tokens, "latency_ms": r.latency_ms,
        "trace_id": r.trace_id, "error": r.error, "created_at": r.created_at.isoformat(),
    }


def _plan_view(db: Session, p: AdaptivePlan, with_exercises: bool) -> dict:
    body = p.plan or {}
    view = {
        "id": p.id, "status": p.status, "trigger": p.trigger, "engine": p.engine, "summary": p.summary,
        "focus_concepts": p.focus_concepts, "diagnosis": p.diagnosis, "error": p.error,
        "strategy": body.get("strategy"), "items": body.get("items", []),
        "generated_count": body.get("generated_count", 0), "seeded_count": body.get("seeded_count", 0),
        "validation_errors": body.get("validation_errors", []),
        "exercise_count": len(body.get("exercise_ids", [])),
        "created_at": p.created_at.isoformat(),
        "completed_at": p.completed_at.isoformat() if p.completed_at else None,
    }
    if with_exercises and body.get("exercise_ids"):
        exs = db.scalars(select(Exercise).where(Exercise.id.in_(body["exercise_ids"]))).all()
        view["exercises"] = [
            {"id": e.id, "type": e.type, "source": e.source, "concepts": [c.key for c in e.concepts],
             "rationale": e.rationale, "difficulty": e.difficulty,
             "preview": public_payload(e.type, e.payload, rng_seed=e.id),
             "answer": display_answer(e.type, e.payload)}
            for e in exs
        ]
    return view


@router.post("/plan")
async def replan(body: PlanIn, background: BackgroundTasks, user: User = Depends(current_user),
                 db: Session = Depends(get_db)):
    tutor_limiter.check(f"u{user.id}")
    if pipeline.is_running(user.id):
        return {"status": "already_running"}
    background.add_task(pipeline.run_pipeline, user.id, "manual", body.focus[:4])
    return {"status": "started"}


@router.post("/simulate")
async def simulate(body: SimulateIn, background: BackgroundTasks, user: User = Depends(current_user),
                   db: Session = Depends(get_db)):
    """Reviewer tool: inject realistic mistakes for a profile, then re-run the tutor on them."""
    tutor_limiter.check(f"u{user.id}")
    result = simulator.inject(db, user, body.profile)
    db.commit()
    if body.run_agents and not pipeline.is_running(user.id):
        background.add_task(pipeline.run_pipeline, user.id, f"simulated:{body.profile}")
        result["pipeline"] = "started"
    return result


@router.get("/chat")
def chat_history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(TutorMessage).where(TutorMessage.user_id == user.id).order_by(TutorMessage.id.desc()).limit(30)
    ).all()[::-1]
    return {"messages": [{"role": m.role, "content": m.content, "blocked": m.blocked,
                          "channel": m.channel} for m in rows]}


@router.post("/chat")
async def chat(body: ChatIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _guard_agent_call(db, user)
    return await duo.chat(db, user, body.message.strip())


@router.post("/explain")
async def explain(body: ExplainIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _guard_agent_call(db, user)
    out = await duo.explain_attempt(db, user, body.attempt_id)
    if out.get("error"):
        raise HTTPException(404, "Attempt not found")
    return out
