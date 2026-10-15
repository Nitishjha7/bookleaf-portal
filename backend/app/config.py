"""
Central configuration, loaded from environment variables.

Everything that changes between environments (DB, secret key, the AI API key)
lives here and is read from the environment — nothing secret is ever hardcoded.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Database ---------------------------------------------------------
    # If DATABASE_URL is set (e.g. the Postgres URL Render/Railway give you),
    # we use it. Otherwise we fall back to a local SQLite file so the project
    # runs out of the box with zero setup.
    database_url: str = "sqlite:///./bookleaf.db"

    # --- Auth / JWT -------------------------------------------------------
    secret_key: str = "dev-secret-change-me-in-production"
    access_token_expire_minutes: int = 60 * 24  # 1 day

    # --- AI / LLM ---------------------------------------------------------
    # The Anthropic API key. Read ONLY on the backend, never shipped to the
    # frontend. If it is missing the app still works (graceful degradation).
    anthropic_api_key: str = ""
    ai_model: str = "claude-3-5-haiku-20241022"
    ai_enabled: bool = True  # master switch; AI also auto-disables if no key

    # --- CORS -------------------------------------------------------------
    # Comma-separated list of allowed frontend origins.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ai_active(self) -> bool:
        """AI is only really usable when enabled AND a key is present."""
        return self.ai_enabled and bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
