import asyncio
import logging
from contextlib import asynccontextmanager

from agents import set_default_openai_key, set_tracing_export_api_key
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import learner, sessions, tutor
from app.core.config import get_settings
from app.seed.seed import run as seed
from app.services.errors import GameError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed()  # idempotent; the free-tier disk can be fresh on every boot
    if settings.openai_api_key:
        # The key is read from env/.env by our settings and handed to the SDK in-process only.
        set_default_openai_key(settings.openai_api_key, use_for_tracing=True)
        set_tracing_export_api_key(settings.openai_api_key)
    # Warm the voice stack in the background so the first voice chat starts fast.
    warm = asyncio.create_task(asyncio.to_thread(_warm_voice))
    yield
    warm.cancel()


def _warm_voice() -> None:
    try:
        from app.voice.routes import warm_up

        warm_up()
    except Exception as e:  # noqa: BLE001  (voice is optional; never block or crash startup)
        logging.getLogger("voice").info("voice warm-up skipped: %s", e)


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=False,  # bearer tokens, no cookies
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(GameError)
async def game_error_handler(_: Request, exc: GameError):
    return JSONResponse(status_code=exc.status, content={"detail": exc.message, "code": exc.code})


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


api = APIRouter(prefix="/api/v1")
api.include_router(learner.router, tags=["learner"])
api.include_router(sessions.router, tags=["lessons"])
api.include_router(tutor.router, tags=["tutor"])
app.include_router(api)

try:  # Voice Smarto is optional: only mounted when its dependencies and keys are present.
    from app.voice.routes import router as voice_router

    app.include_router(voice_router, prefix="/api/v1", tags=["voice"])
except ImportError as e:  # pragma: no cover
    logging.getLogger("voice").info("voice disabled: %s", e)


@app.get("/health")
def health():
    return {"ok": True, "agents": settings.agents_enabled}
