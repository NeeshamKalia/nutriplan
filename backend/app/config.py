from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nutriplan:nutriplan@localhost:5432/nutriplan"

    # Auth
    JWT_SECRET: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    JWT_REFRESH_EXPIRATION_DAYS: int = 30

    # Gemini (primary — free tier)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_CHEAP_MODEL: str = "gemini-2.0-flash-lite"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"

    # RAG (Phase 9)
    EMBEDDING_DIMENSION: int = 768
    RAG_TOP_K: int = 3
    RAG_MIN_SIMILARITY: float = 0.35

    # OpenAI (fallback — paid, optional for MVP)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_CHEAP_MODEL: str = "gpt-4o-mini"

    # WhatsApp
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""

    # LangSmith (Phase 9 — optional LLM tracing)
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_PROJECT: str = "nutriplan"

    # AI plan generator backend (Phase 4/9/10)
    # simple = direct Gemini/OpenAI | langchain = Phase 9 | langgraph = Phase 10
    PLAN_GENERATOR_BACKEND: str = "langgraph"

    # Redis cache (Phase 10)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 300

    # Scheduler (Phase 10)
    ENABLE_SCHEDULER: bool = False
    REMINDER_MORNING_HOUR: int = 7
    REMINDER_WEEKLY_HOUR: int = 9

    # App
    APP_NAME: str = "NutriPlan"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_production_settings(self):
        if not self.DEBUG and self.JWT_SECRET == "change-this-in-production":
            raise ValueError("JWT_SECRET must be changed from the default in production (DEBUG=False).")
        return self


settings = Settings()
