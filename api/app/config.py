from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "zimran-hackathon-api"
    # Comma-separated list of allowed frontend origins
    cors_origins: str = "http://localhost:3000"

    # LLM keys (fill in .env, never commit)
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Postgres in production (Neon/Supabase URL is fine as-is). Empty = local SQLite file.
    database_url: str = ""
    # Base URL of the web app, used to build invite links (empty = relative links).
    web_base_url: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
