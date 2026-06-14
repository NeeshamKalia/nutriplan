"""Structured JSON logging with per-request context.

Uses Python stdlib logging + contextvars for async-safe request tracking.
Every log line includes request_id, user_id, and correlation_id.
"""

import json
import logging
import sys
from contextvars import ContextVar

# Context variables — set per-request via middleware
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="-")
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="-")


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
            "user_id": user_id_ctx.get(),
            "correlation_id": correlation_id_ctx.get(),
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Include any extra fields passed via logger.info("msg", extra={...})
        for key in ("client_id", "dietitian_id", "duration_ms", "tokens", "cost"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure root logger with JSON formatter."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.setLevel(log_level.upper())
    root.handlers = [handler]

    # Quiet down noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. Use __name__ for automatic module-based naming."""
    return logging.getLogger(name)
