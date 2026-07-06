import warnings
from enum import Enum

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


_PLACEHOLDER_KEYS = {
    "your-gemini-key-here",
    "sk-your-key-here",
    "change-this-in-production",
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    In production (DEBUG=False), the app fails fast if critical security
    settings are missing or insecure. This prevents accidental deployment
    with dev defaults.
    """

    # Environment
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nutriplan:nutriplan@localhost:5432/nutriplan"

    # Auth
    JWT_SECRET: str = ""
    ENCRYPTION_KEY: str = ""  # Fernet key for field-level encryption
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
    SQL_ECHO: bool = False  # Separate from DEBUG to avoid leaking query data
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_production(self) -> bool:
        """True when running in production mode (DEBUG=False or ENVIRONMENT=production)."""
        return not self.DEBUG or self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def has_ai_keys(self) -> bool:
        """True if at least one valid (non-placeholder) AI key is configured."""
        return bool(
            (self.GEMINI_API_KEY and self.GEMINI_API_KEY not in _PLACEHOLDER_KEYS)
            or (self.OPENAI_API_KEY and self.OPENAI_API_KEY not in _PLACEHOLDER_KEYS)
        )

    @model_validator(mode="after")
    def validate_production_settings(self):
        """Fail fast on missing/insecure config in production.

        In development, issues are logged as warnings instead of errors
        so local dev and tests aren't blocked.
        """
        # ── Auto-fix: Render/Heroku provide postgresql:// but we need asyncpg ──
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        elif self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        errors: list[str] = []

        if self.is_production:
            # ── Security: authentication secrets ─────────────────
            if not self.JWT_SECRET or self.JWT_SECRET in _PLACEHOLDER_KEYS:
                errors.append(
                    "JWT_SECRET must be set to a strong random value in production. "
                    "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )

            if not self.ENCRYPTION_KEY:
                errors.append(
                    "ENCRYPTION_KEY must be set in production for field-level encryption. "
                    "Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                )

            # ── Security: CORS must not be open ──────────────────
            if "*" in self.CORS_ORIGINS:
                errors.append("CORS_ORIGINS must not contain '*' in production.")

            if any("localhost" in origin for origin in self.CORS_ORIGINS):
                errors.append(
                    "CORS_ORIGINS contains localhost — update to your production domain."
                )

            # ── Security: frontend URL ───────────────────────────
            if "localhost" in self.FRONTEND_URL:
                errors.append(
                    "FRONTEND_URL is still localhost — set to your production URL."
                )

            # ── Database: no default credentials ─────────────────
            if "nutriplan:nutriplan@localhost" in self.DATABASE_URL:
                errors.append(
                    "DATABASE_URL uses default local credentials — "
                    "set to your managed PostgreSQL URL."
                )

            if errors:
                raise ValueError(
                    "Production configuration errors:\n  - " + "\n  - ".join(errors)
                )

        else:
            # ── Dev warnings (non-blocking) ──────────────────────
            if not self.GEMINI_API_KEY or self.GEMINI_API_KEY in _PLACEHOLDER_KEYS:
                warnings.warn(
                    "GEMINI_API_KEY is not set — AI features will not work.",
                    stacklevel=1,
                )

        return self


settings = Settings()
