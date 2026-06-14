"""NutriPlan — AI-powered practice OS for Indian nutritionists.

FastAPI application entry point with structured logging and CORS middleware.
"""

import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logger import (
    correlation_id_ctx,
    get_logger,
    request_id_ctx,
    setup_logging,
    user_id_ctx,
)

# Initialize structured logging before anything else
setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered practice OS for Indian nutritionists",
    version="0.1.0",
)

# CORS — allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Inject request_id and correlation_id into every request context."""
    rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    cid = request.headers.get("X-Correlation-ID", rid)
    request_id_ctx.set(rid)
    correlation_id_ctx.set(cid)
    # user_id_ctx is set later by the auth dependency

    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {"status": "ok", "app": settings.APP_NAME}
