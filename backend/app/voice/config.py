"""Voice settings (env vars), mirroring the Cat agent's configuration."""
import os
from dataclasses import dataclass

from app.core.config import get_settings

LLM_BASE = {"cerebras": "CEREBRAS_API_KEY", "openai": "OPENAI_API_KEY"}
LLM_DEFAULT_MODEL = {"cerebras": "gpt-oss-120b", "openai": "gpt-4.1-mini"}


@dataclass(frozen=True)
class VoiceConfig:
    deepgram_api_key: str
    llm_provider: str
    llm_api_key: str
    llm_model: str
    stt_model: str
    stt_language: str
    tts_voice: str
    vad_stop_secs: float
    max_session_secs: int
    daily_sessions: int  # per learner
    ip_daily_sessions: int  # per IP, so making new guests doesn't reset it


def load_voice_config() -> VoiceConfig | None:
    """None when voice isn't configured (the UI then hides the mic button)."""
    _load_dotenv_once()
    provider = os.getenv("VOICE_LLM_PROVIDER", "cerebras").lower()
    deepgram = os.getenv("DEEPGRAM_API_KEY")
    llm_key = os.getenv(LLM_BASE.get(provider, "CEREBRAS_API_KEY")) or (
        get_settings().openai_api_key if provider == "openai" else None
    )
    if not deepgram or not llm_key:
        return None
    return VoiceConfig(
        deepgram_api_key=deepgram,
        llm_provider=provider,
        llm_api_key=llm_key,
        llm_model=os.getenv("VOICE_LLM_MODEL", LLM_DEFAULT_MODEL.get(provider, "gpt-oss-120b")),
        stt_model=os.getenv("VOICE_STT_MODEL", "nova-3-general"),
        stt_language=os.getenv("VOICE_STT_LANGUAGE", "multi"),
        tts_voice=os.getenv("VOICE_TTS_VOICE", "aura-2-selena-es"),
        vad_stop_secs=float(os.getenv("VOICE_VAD_STOP_SECS", "0.3")),
        max_session_secs=int(os.getenv("VOICE_MAX_SESSION_SECS", "180")),
        daily_sessions=int(os.getenv("VOICE_DAILY_SESSIONS", "25")),
        ip_daily_sessions=int(os.getenv("VOICE_DAILY_SESSIONS_PER_IP", "25")),
    )


_loaded = False


def _load_dotenv_once() -> None:
    """pydantic-settings reads .env for its own fields only; voice keys are plain env vars."""
    global _loaded
    if _loaded:
        return
    _loaded = True
    path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
