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

    # Database. Locally a SQLite file; on Vercel set DATABASE_URL to Postgres (Neon/Supabase):
    # serverless functions don't keep files between requests.
    database_url: str = "sqlite:///./casefile.db"

    # Stripe (test mode keys: sk_test_..., whsec_...)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    # Where Stripe Checkout sends the player back (the web app, not the API)
    public_web_url: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
