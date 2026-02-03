FROM python:3.11-slim as builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system --no-cache -r pyproject.toml

FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
COPY docker-entrypoint.sh ./docker-entrypoint.sh

# Create non-root user first
RUN useradd -m -u 1000 appuser

# Make entrypoint executable and set ownership
RUN chmod +x ./docker-entrypoint.sh && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
