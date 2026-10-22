from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # sqlite by default so it runs without any setup; set DATABASE_URL for postgres
    database_url: str = "sqlite:///./bookleaf.db"

    secret_key: str = "dev-secret-change-me-in-production"
    access_token_expire_minutes: int = 60 * 24

    # Gemini key from https://aistudio.google.com/apikey - app works without it,
    # it just falls back to the keyword rules
    gemini_api_key: str = ""
    ai_model: str = "gemini-3.8-flash"
    # tried in order if the main model is out of quota or unavailable (quotas are per model)
    ai_fallback_models: str = "gemini-3.5-flash,gemini-flash-lite-latest"
    ai_enabled: bool = True

    # comma separated
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def _clean_key(cls, v):
        # pasted keys often come with spaces, newlines or quotes
        return (v or "").strip().strip("'\"")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ai_model_chain(self) -> list[str]:
        extra = [m.strip() for m in self.ai_fallback_models.split(",") if m.strip()]
        return [self.ai_model] + [m for m in extra if m != self.ai_model]

    @property
    def ai_active(self) -> bool:
        return self.ai_enabled and bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
