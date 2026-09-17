# Production-ready Dockerfile for LeaseLens FastAPI Backend
# Target Platform: Google Cloud Run (Fully Managed Container Platform)

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Set container working directory
WORKDIR /app

# Install system dependencies (curl for healthchecks, build tools if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies first for efficient Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source directories and files
COPY main.py .
COPY agents/ ./agents/
COPY schemas/ ./schemas/
COPY data/ ./data/

# Run as non-root user for cloud security hardening
RUN useradd -u 1000 appuser && chown -R appuser /app
USER appuser

# Expose HTTP port dynamically using Cloud Run's PORT env var
EXPOSE ${PORT}

# Healthcheck for container liveness
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Launch uvicorn dynamically bound to $PORT with exec signal forwarding
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
