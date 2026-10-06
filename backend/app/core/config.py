import logging
import secrets
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Everything sensitive comes from env vars / .env only."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Smartalingo API"
    database_url: str = "sqlite:///./data/app.db"

    # No baked-in default: a known secret would let anyone forge tokens if the env var were forgotten.
    jwt_secret: str = Field(default="", repr=False)
    jwt_ttl_days: int = 30

    cors_origins: str = "http://localhost:3000"
    cors_origin_regex: str | None = None

    openai_api_key: str | None = Field(default=None, repr=False)
    openai_model: str = "gpt-5-mini"
    agent_daily_budget: int = 15
    agent_max_turns: int = 8

    demo_mode: bool = True

    # Gamification tuning
    max_hearts: int = 5
    heart_regen_minutes: int = 240
    refill_hearts_gem_cost: int = 350
    streak_freeze_gem_cost: int = 200
    xp_per_lesson: int = 10
    xp_perfect_bonus: int = 5

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def agents_enabled(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if len(s.jwt_secret) < 32:
        # Unset or weak: use a random per-process secret (existing tokens stop working on restart, and the
        # frontend quietly creates a new guest). Set JWT_SECRET in production to keep sessions across restarts.
        logging.getLogger("config").warning("JWT_SECRET missing or shorter than 32 chars; using a random secret")
        s.jwt_secret = secrets.token_urlsafe(48)
    return s
