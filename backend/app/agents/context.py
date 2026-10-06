"""Run context shared by every agent and tool in one tutor run.

Tools receive it via `RunContextWrapper[TutorContext]`, so they always act on the learner the run
was started for: the LLM can never pick a user id (no cross-learner data access by construction).
"""
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.db import SessionLocal


@dataclass
class TutorContext:
    user_id: int
    session_factory: Callable[[], Session] = SessionLocal
    focus_hint: list[str] = field(default_factory=list)  # concepts the learner explicitly asked for
    requested_practice: list[str] = field(default_factory=list)  # set by Duo's create_practice tool
