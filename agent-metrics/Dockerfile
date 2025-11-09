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

COPY agent-metrics/pyproject.toml ./agent-metrics/
COPY common-ai ./common-ai/

RUN pip install --no-cache-dir uv && \
    uv sync --directory agent-metrics && \
    uv run --directory agent-metrics --with pip opentelemetry-bootstrap -a install

COPY agent-metrics/agent_metrics ./agent-metrics/agent_metrics/

EXPOSE 8003

CMD ["uv", "run", "--directory", "agent-metrics", "opentelemetry-instrument", "uvicorn", "agent_metrics.main:app", "--host", "0.0.0.0", "--port", "8003"]

# ============================================
# Prod stage: Optimized production image
# ============================================
FROM base AS prod

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY agent-metrics/pyproject.toml ./agent-metrics/
COPY common-ai ./common-ai/

RUN pip install --no-cache-dir uv && \
    uv sync --directory agent-metrics --no-dev && \
    uv run --directory agent-metrics --no-dev --with pip opentelemetry-bootstrap -a install

COPY agent-metrics/agent_metrics ./agent-metrics/agent_metrics/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8003

CMD ["uv", "run", "--directory", "agent-metrics", "opentelemetry-instrument", "uvicorn", "agent_metrics.main:app", "--host", "0.0.0.0", "--port", "8003"]

# ============================================
# Final stage: Select based on BUILD_TARGET
# ============================================
FROM ${BUILD_TARGET}
