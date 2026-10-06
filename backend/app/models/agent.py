"""Persistence for the agentic tutor: plans it produced, every agent run (observability), chat."""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import utcnow
from app.core.db import Base


class AdaptivePlan(Base):
    __tablename__ = "adaptive_plans"
    __table_args__ = (Index("ix_plans_user_status", "user_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|ready|consumed|failed|superseded
    trigger: Mapped[str] = mapped_column(String(32))  # lesson_complete | onboarding | manual | chat
    engine: Mapped[str] = mapped_column(String(16), default="agents")  # agents | rules (fallback)
    diagnosis: Mapped[dict | None] = mapped_column(JSON)
    plan: Mapped[dict | None] = mapped_column(JSON)
    focus_concepts: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[str | None] = mapped_column(Text)  # learner-facing message from "Smarto"
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime)


class AgentRun(Base):
    """One row per agent invocation, for observability and budgeting.

    kind='pipeline' | 'chat' | 'explain' | 'voice' rows count toward the learner's daily budget;
    kind='step' rows are the individual agents inside a pipeline (children via parent_id).
    """

    __tablename__ = "agent_runs"
    __table_args__ = (Index("ix_runs_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("adaptive_plans.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("agent_runs.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))
    agent_name: Mapped[str] = mapped_column(String(48))
    status: Mapped[str] = mapped_column(String(16), default="running")  # running|ok|error|blocked|fallback
    input_summary: Mapped[str | None] = mapped_column(Text)
    output: Mapped[dict | None] = mapped_column(JSON)
    tool_calls: Mapped[list] = mapped_column(JSON, default=list)
    model: Mapped[str | None] = mapped_column(String(48))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    trace_id: Mapped[str | None] = mapped_column(String(64))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class TutorMessage(Base):
    __tablename__ = "tutor_messages"
    __table_args__ = (Index("ix_tutor_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String(8), default="text")  # text | voice
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
