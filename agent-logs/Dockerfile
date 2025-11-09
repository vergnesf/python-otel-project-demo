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

COPY agent-logs/pyproject.toml ./agent-logs/
COPY common-ai ./common-ai/

RUN pip install --no-cache-dir uv && \
    uv sync --directory agent-logs && \
    uv run --directory agent-logs --with pip opentelemetry-bootstrap -a install

COPY agent-logs/agent_logs ./agent-logs/agent_logs/

EXPOSE 8002

CMD ["uv", "run", "--directory", "agent-logs", "opentelemetry-instrument", "uvicorn", "agent_logs.main:app", "--host", "0.0.0.0", "--port", "8002"]

# ============================================
# Prod stage: Optimized production image
# ============================================
FROM base AS prod

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY agent-logs/pyproject.toml ./agent-logs/
COPY common-ai ./common-ai/

RUN pip install --no-cache-dir uv && \
    uv sync --directory agent-logs --no-dev && \
    uv run --directory agent-logs --no-dev --with pip opentelemetry-bootstrap -a install

COPY agent-logs/agent_logs ./agent-logs/agent_logs/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8002

CMD ["uv", "run", "--directory", "agent-logs", "opentelemetry-instrument", "uvicorn", "agent_logs.main:app", "--host", "0.0.0.0", "--port", "8002"]

# ============================================
# Final stage: Select based on BUILD_TARGET
# ============================================
FROM ${BUILD_TARGET}
