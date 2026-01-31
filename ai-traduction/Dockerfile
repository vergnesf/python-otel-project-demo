ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"
ARG BUILD_TARGET=prod

# ============================================
# Base stage: Common setup for all targets
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON} AS base

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHON_JIT=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# ============================================
# Dev stage: Development with hot reload
# ============================================
FROM base AS dev

COPY ai-traduction/pyproject.toml /app/ai-traduction/
COPY common-ai /app/common-ai/

WORKDIR /app/ai-traduction

RUN pip install --no-cache-dir uv && \
    uv add pip && \
    uv run --no-dev opentelemetry-bootstrap -a install

COPY ai-traduction/ai_traduction /app/ai-traduction/ai_traduction/

EXPOSE 8002

CMD ["uv", "run", "--no-dev", "opentelemetry-instrument", "uvicorn", "ai_traduction.main:app", "--host", "0.0.0.0", "--port", "8002"]

# ============================================
# Prod stage: Optimized production image
# ============================================
FROM base AS prod

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY ai-traduction/pyproject.toml /app/ai-traduction/
COPY common-ai /app/common-ai/

WORKDIR /app/ai-traduction

RUN pip install --no-cache-dir uv && \
    uv add pip && \
    uv run --no-dev opentelemetry-bootstrap -a install

COPY ai-traduction/ai_traduction /app/ai-traduction/ai_traduction/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8002

CMD ["uv", "run", "--no-dev", "opentelemetry-instrument", "uvicorn", "ai_traduction.main:app", "--host", "0.0.0.0", "--port", "8002"]

# ============================================
# Final stage: Select based on BUILD_TARGET
# ============================================
FROM ${BUILD_TARGET}
