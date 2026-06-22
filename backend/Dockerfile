# Production Dockerfile for NutriPlan Backend
# SD-008: Multi-stage build, non-root user, no --reload, signal handling

# ── Stage 1: Build wheels ────────────────────────────────────────
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────
FROM python:3.11-slim

# Create a non-root user
RUN adduser --disabled-password --gecos '' nutriplan

WORKDIR /app

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir /wheels/*

COPY . .

# Set permissions
RUN chown -R nutriplan:nutriplan /app
USER nutriplan

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with proper signal handling and multiple workers for production
# No --reload flag (development only)
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
