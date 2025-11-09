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

COPY agent-traces/pyproject.toml ./agent-traces/
COPY common-ai ./common-ai/

RUN pip install --no-cache-dir uv && \
    uv sync --directory agent-traces && \
    uv run --directory agent-traces opentelemetry-bootstrap -a install

COPY agent-traces/agent_traces ./agent-traces/agent_traces/

EXPOSE 8004

CMD ["uv", "run", "--directory", "agent-traces", "opentelemetry-instrument", "uvicorn", "agent_traces.main:app", "--host", "0.0.0.0", "--port", "8004", "--reload"]

# ============================================
# Prod stage: Optimized production image
# ============================================
FROM base AS prod

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY agent-traces/pyproject.toml ./agent-traces/
COPY common-ai ./common-ai/

RUN pip install --no-cache-dir uv && \
    uv sync --directory agent-traces --no-dev && \
    uv run --directory agent-traces --no-dev opentelemetry-bootstrap -a install

COPY agent-traces/agent_traces ./agent-traces/agent_traces/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8004

CMD ["uv", "run", "--directory", "agent-traces", "opentelemetry-instrument", "uvicorn", "agent_traces.main:app", "--host", "0.0.0.0", "--port", "8004"]

# ============================================
# Final stage: Select based on BUILD_TARGET
# ============================================
FROM ${BUILD_TARGET}
