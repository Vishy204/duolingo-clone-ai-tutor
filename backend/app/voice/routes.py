"""Voice endpoints: availability check + the WebSocket the browser's Pipecat client connects to.

Security: the browser can't set headers on a WebSocket, so it first exchanges its JWT (sent as a
normal Authorization header) for a single-use 60s ticket, and only the ticket goes in the URL.
Origins are restricted to the frontend, each learner gets one live session at a time (a new one
replaces a stale one, e.g. after navigating away), and sessions are capped in length and per day.
"""
import asyncio
import re
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.clock import utcnow
from app.core.config import get_settings
from app.core.db import SessionLocal, get_db
from app.core.rate_limit import tutor_limiter
from app.models import AgentRun, User
from app.voice.config import load_voice_config

router = APIRouter(prefix="/voice")
_live: dict[int, WebSocket] = {}
# Single-use, short-lived tickets: the WebSocket URL never carries the long-lived JWT (URLs end up in
# access logs). In-memory is fine for one instance; move to Redis when scaling out.
_tickets: dict[str, tuple[int, float]] = {}
TICKET_TTL = 60


def _issue_ticket(user_id: int) -> str:
    now = time.monotonic()
    for k, (_, exp) in list(_tickets.items()):
        if exp < now:
            del _tickets[k]
    ticket = secrets.token_urlsafe(24)
    _tickets[ticket] = (user_id, now + TICKET_TTL)
    return ticket


def _redeem_ticket(ticket: str) -> int | None:
    entry = _tickets.pop(ticket, None)
    if entry is None or entry[1] < time.monotonic():
        return None
    return entry[0]


def _sessions_today(db: Session, user_id: int) -> int:
    start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return db.scalar(
        select(func.count(AgentRun.id)).where(
            AgentRun.user_id == user_id, AgentRun.kind == "voice", AgentRun.created_at >= start
        )
    ) or 0


@router.get("/status")
def status(user: User = Depends(current_user), db: Session = Depends(get_db)):
    cfg = load_voice_config()
    if cfg is None:
        return {"enabled": False}
    return {
        "enabled": True,
        "max_session_secs": cfg.max_session_secs,
        "sessions_left_today": max(0, cfg.daily_sessions - _sessions_today(db, user.id)),
    }


@router.post("/ticket")
def ticket(user: User = Depends(current_user), db: Session = Depends(get_db)):
    cfg = load_voice_config()
    if cfg is None:
        raise HTTPException(503, "Voice is not configured")
    if _sessions_today(db, user.id) >= cfg.daily_sessions:
        raise HTTPException(429, "You've used today's voice sessions. Back tomorrow!")
    tutor_limiter.check(f"u{user.id}")
    return {"ticket": _issue_ticket(user.id), "expires_in": TICKET_TTL}


@router.websocket("/ws")
async def voice_ws(websocket: WebSocket, ticket: str = ""):
    cfg = load_voice_config()
    user_id = _redeem_ticket(ticket) if ticket else None
    origin = websocket.headers.get("origin", "")
    s = get_settings()
    origin_ok = not origin or origin in s.cors_origin_list or (
        s.cors_origin_regex and re.fullmatch(s.cors_origin_regex, origin)
    )
    # Accept before rejecting so the browser gets a real close code + reason instead of a bare 1006.
    if cfg is None or user_id is None or not origin_ok:
        await websocket.accept()
        reason = ("voice unavailable" if cfg is None
                  else "session expired, try again" if user_id is None else "origin not allowed")
        await websocket.close(code=4401 if user_id is None else 4403, reason=reason)
        return
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None or user.is_bot or _sessions_today(db, user_id) >= cfg.daily_sessions:
            await websocket.accept()
            await websocket.close(code=4429, reason="daily voice limit reached")
            return
    # One live session per learner: the newest wins, so a forgotten tab can't lock them out.
    stale = _live.pop(user_id, None)
    if stale is not None:
        try:
            await stale.close(code=4000, reason="replaced by a new session")
        except Exception:  # noqa: BLE001
            pass
    with SessionLocal() as db:
        run = AgentRun(user_id=user_id, kind="voice", agent_name="Voice Duo", status="running",
                       model=f"{cfg.llm_provider}/{cfg.llm_model}", input_summary="voice session", tool_calls=[])
        db.add(run)
        db.commit()
        run_id = run.id

    # Imported lazily: pipecat is heavy and only needed when someone actually talks.
    from pipecat.serializers.protobuf import ProtobufFrameSerializer
    from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams, FastAPIWebsocketTransport
    from pipecat.workers.runner import WorkerRunner

    from app.voice.pipeline import build_worker

    await websocket.accept()
    _live[user_id] = websocket
    started = time.perf_counter()
    try:
        transport = FastAPIWebsocketTransport(
            websocket,
            FastAPIWebsocketParams(
                audio_in_enabled=True, audio_out_enabled=True, add_wav_header=False,
                serializer=ProtobufFrameSerializer(), session_timeout=cfg.max_session_secs,
            ),
        )
        worker = build_worker(transport, cfg, user_id)
        runner = WorkerRunner(handle_sigint=False)

        @transport.event_handler("on_client_disconnected")
        async def on_disconnected(transport, ws):
            await worker.cancel()

        @transport.event_handler("on_session_timeout")
        async def on_timeout(transport, ws):
            await worker.cancel()

        await runner.add_workers(worker)
        await asyncio.wait_for(runner.run(), timeout=cfg.max_session_secs + 15)
    except (TimeoutError, WebSocketDisconnect):
        pass
    except Exception:  # noqa: BLE001
        logger.exception("voice session crashed")
    finally:
        if _live.get(user_id) is websocket:
            del _live[user_id]
        with SessionLocal() as db:
            run = db.get(AgentRun, run_id)
            run.status = "ok"
            run.latency_ms = int((time.perf_counter() - started) * 1000)
            db.commit()
