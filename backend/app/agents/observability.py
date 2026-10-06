"""Run agents with full observability: every invocation becomes an AgentRun row (status, latency,
token usage, tool calls, structured output, trace id) that powers the "Tutor Brain" page and the
per-learner budget. SDK tracing is also on, so the same runs appear in the OpenAI Traces dashboard."""
import json
import time
from typing import Any

from agents import Agent, Runner, ToolCallItem, get_current_trace
from pydantic import BaseModel
from sqlalchemy import func, select

from app.agents.context import TutorContext
from app.core.clock import utcnow
from app.core.config import get_settings
from app.models import AgentRun

# Voice has its own limits (per learner and per IP, see app/voice/routes.py).
BUDGETED_KINDS = ("pipeline", "chat", "explain")


def start_run(user_id: int, kind: str, agent_name: str, input_summary: str, plan_id: int | None = None,
              parent_id: int | None = None, ctx_factory=None) -> int:
    from app.core.db import SessionLocal

    with (ctx_factory or SessionLocal)() as db:
        trace = get_current_trace()
        run = AgentRun(
            user_id=user_id, kind=kind, agent_name=agent_name, status="running", plan_id=plan_id,
            parent_id=parent_id, input_summary=input_summary[:4000], tool_calls=[],
            model=get_settings().openai_model, trace_id=trace.trace_id if trace else None,
        )
        db.add(run)
        db.commit()
        return run.id


def finish_run(run_id: int, *, status: str, output: Any = None, error: str | None = None,
               usage: tuple[int, int] = (0, 0), latency_ms: int = 0, tool_calls: list | None = None,
               model: str | None = None, ctx_factory=None) -> None:
    from app.core.db import SessionLocal

    with (ctx_factory or SessionLocal)() as db:
        run = db.get(AgentRun, run_id)
        if run is None:
            return
        run.status = status
        run.output = _jsonable(output)
        run.error = (error or "")[:2000] or None
        run.input_tokens, run.output_tokens = usage
        run.latency_ms = latency_ms
        if tool_calls is not None:
            run.tool_calls = tool_calls
        if model:
            run.model = model
        db.commit()


def _jsonable(output: Any) -> Any:
    if output is None:
        return None
    if isinstance(output, BaseModel):
        return output.model_dump()
    if isinstance(output, (dict, list)):
        return json.loads(json.dumps(output, default=str))
    return {"text": str(output)}


async def run_step(agent: Agent[TutorContext], input: str | list, ctx: TutorContext, *, kind: str = "step",
                   plan_id: int | None = None, parent_id: int | None = None, max_turns: int | None = None):
    """Runner.run + AgentRun bookkeeping. Re-raises after recording the failure."""
    summary = input if isinstance(input, str) else json.dumps(input, default=str)[:2000]
    run_id = start_run(ctx.user_id, kind, agent.name, summary, plan_id, parent_id, ctx.session_factory)
    t0 = time.perf_counter()
    try:
        result = await Runner.run(agent, input, context=ctx, max_turns=max_turns or get_settings().agent_max_turns)
    except Exception as e:
        finish_run(run_id, status="blocked" if "Tripwire" in type(e).__name__ else "error",
                   error=f"{type(e).__name__}: {e}", latency_ms=int((time.perf_counter() - t0) * 1000),
                   ctx_factory=ctx.session_factory)
        raise
    usage = result.context_wrapper.usage
    tool_calls = []
    for item in result.new_items:
        if isinstance(item, ToolCallItem):
            raw = item.raw_item
            name = getattr(raw, "name", None) or (raw.get("name") if isinstance(raw, dict) else None)
            args = getattr(raw, "arguments", None) or (raw.get("arguments") if isinstance(raw, dict) else None)
            tool_calls.append({"tool": name, "arguments": args})
    finish_run(
        run_id, status="ok", output=result.final_output,
        usage=(usage.input_tokens, usage.output_tokens),
        latency_ms=int((time.perf_counter() - t0) * 1000), tool_calls=tool_calls,
        ctx_factory=ctx.session_factory,
    )
    return result, run_id


def budget_used_today(db, user_id: int) -> int:
    start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return db.scalar(
        select(func.count(AgentRun.id)).where(
            AgentRun.user_id == user_id, AgentRun.kind.in_(BUDGETED_KINDS), AgentRun.created_at >= start
        )
    ) or 0


def budget_left(db, user_id: int) -> int:
    return max(0, get_settings().agent_daily_budget - budget_used_today(db, user_id))
