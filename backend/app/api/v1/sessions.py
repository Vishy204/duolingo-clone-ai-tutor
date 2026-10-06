"""The lesson loop: start a session, answer exercises (graded server-side), complete it.
Completing a session kicks off the adaptive tutor pipeline in the background."""
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.agents.pipeline import run_pipeline
from app.api.deps import current_user
from app.core.db import get_db
from app.core.rate_limit import answer_limiter
from app.models import User
from app.schemas.api import AnswerIn, SessionIn
from app.services import lesson_engine

router = APIRouter(prefix="/sessions")


@router.post("")
def start(body: SessionIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    session = lesson_engine.start_session(db, user, body.mode, body.lesson_id, body.skill_id, body.plan_id)
    db.commit()
    return lesson_engine.session_view(db, session, user)


@router.post("/{session_id}/answers")
def answer(session_id: int, body: AnswerIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    answer_limiter.check(f"u{user.id}")
    session = lesson_engine.get_owned_session(db, user, session_id)
    result = lesson_engine.submit_answer(db, user, session, body.exercise_id, body.answer, body.time_ms)
    db.commit()
    return result


@router.post("/{session_id}/complete")
def complete(session_id: int, background: BackgroundTasks, user: User = Depends(current_user),
             db: Session = Depends(get_db)):
    session = lesson_engine.get_owned_session(db, user, session_id)
    summary = lesson_engine.complete_session(db, user, session)
    db.commit()
    # The learner sees the celebration screen immediately; the tutor thinks in the background.
    background.add_task(run_pipeline, user.id, f"{session.mode}_complete")
    summary["tutor_updating"] = True
    return summary


@router.post("/{session_id}/quit")
def quit_session(session_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    session = lesson_engine.get_owned_session(db, user, session_id)
    if session.status == "active":
        session.status = "abandoned"
        db.commit()
    return {"status": session.status}
