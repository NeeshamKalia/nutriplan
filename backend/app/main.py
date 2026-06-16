"""NutriPlan — AI-powered practice OS for Indian nutritionists.

FastAPI application entry point with structured logging and CORS middleware.
"""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logger import (
    correlation_id_ctx,
    get_logger,
    request_id_ctx,
    setup_logging,
)
from app.core.redis import close_redis
from app.scheduler.reminders import start_scheduler, stop_scheduler
from app.routers.v1 import auth, clients, plans, foods, dashboard, progress, articles, protocols
from app.routers import webhook, public, p_pages

# Initialize structured logging before anything else
setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered practice OS for Indian nutritionists",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Webhook (Not versioned) ---
app.include_router(webhook.router)

# --- Public page routes (/p/*) ---
app.include_router(p_pages.router)

# --- Versioned API routes (/api/v1/*) ---
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth.router)
api_v1.include_router(clients.router)
api_v1.include_router(plans.clients_router)
api_v1.include_router(plans.plans_router)
api_v1.include_router(foods.router)
api_v1.include_router(dashboard.router)
api_v1.include_router(progress.router)
api_v1.include_router(articles.router)
api_v1.include_router(protocols.router)
api_v1.include_router(public.router)
app.include_router(api_v1)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Inject request_id and correlation_id into every request context."""
    rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    cid = request.headers.get("X-Correlation-ID", rid)
    request_id_ctx.set(rid)
    correlation_id_ctx.set(cid)
    # user_id_ctx is set later by the auth dependency

    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} duration_ms={duration_ms}"
    )
    response.headers["X-Request-ID"] = rid
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {"status": "ok", "app": settings.APP_NAME}
