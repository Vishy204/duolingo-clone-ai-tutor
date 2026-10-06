from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Everything sensitive comes from env vars / .env only."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Duolingo Clone API"
    database_url: str = "sqlite:///./data/app.db"

    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_ttl_days: int = 30

    cors_origins: str = "http://localhost:3000"
    cors_origin_regex: str | None = None

    openai_api_key: str | None = Field(default=None, repr=False)
    openai_model: str = "gpt-5-mini"
    agent_daily_budget: int = 40
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
    return Settings()
