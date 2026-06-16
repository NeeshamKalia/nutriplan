FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

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

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
