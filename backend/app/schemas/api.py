"""Request bodies (responses are plain dicts built by the services; see README for shapes)."""
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class GuestIn(BaseModel):
    name: str | None = Field(default=None, max_length=40)


class SettingsIn(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=40)
    daily_goal_xp: Literal[10, 20, 30, 50] | None = None
    sound: bool | None = None
    dark_mode: bool | None = None


class SessionIn(BaseModel):
    mode: Literal["lesson", "practice", "personalized", "legendary"] = "lesson"
    lesson_id: int | None = None
    skill_id: int | None = None


class AnswerIn(BaseModel):
    exercise_id: int
    answer: dict[str, Any]
    time_ms: int | None = Field(default=None, ge=0, le=3_600_000)

    @field_validator("answer")
    @classmethod
    def small_answer(cls, v: dict) -> dict:
        allowed = {"choice", "text", "tokens", "mistakes"}
        v = {k: v[k] for k in v if k in allowed}
        if isinstance(v.get("text"), str):
            v["text"] = v["text"][:200]
        if isinstance(v.get("tokens"), list):
            v["tokens"] = [str(t)[:40] for t in v["tokens"][:30]]
        if isinstance(v.get("choice"), str):
            v["choice"] = v["choice"][:60]
        if "mistakes" in v:
            try:
                v["mistakes"] = max(0, min(int(v["mistakes"]), 50))
            except (TypeError, ValueError):
                v["mistakes"] = 0
        return v


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=500)


class ExplainIn(BaseModel):
    attempt_id: int


class PlanIn(BaseModel):
    focus: list[str] = Field(default_factory=list, max_length=4)


class SimulateIn(BaseModel):
    profile: Literal["gender", "accents", "production", "word_order", "verbs"]
    run_agents: bool = True
