ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"
ARG BUILD_TARGET=prod

# ============================================
# Base stage: Common setup for all targets
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON} AS base

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y curl unzip && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHON_JIT=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# ============================================
# Dev stage: Development with hot reload
# ============================================
FROM base AS dev

COPY agent-ui/pyproject.toml ./pyproject.toml

RUN pip install --no-cache-dir uv && \
    uv sync

COPY agent-ui/agent_ui ./agent_ui
COPY agent-ui/rxconfig.py ./rxconfig.py

RUN uv run reflex init

EXPOSE 3002 8000

CMD ["uv", "run", "reflex", "run", "--env", "dev", "--loglevel", "info"]

# ============================================
# Prod stage: Optimized production image
# ============================================
FROM base AS prod

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY agent-ui/pyproject.toml ./pyproject.toml

RUN pip install --no-cache-dir uv && \
    uv sync --no-dev

COPY agent-ui/agent_ui ./agent_ui
COPY agent-ui/rxconfig.py ./rxconfig.py

RUN uv run reflex init

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 3002 8000

CMD ["uv", "run", "reflex", "run", "--env", "prod", "--loglevel", "info"]

# ============================================
# Final stage: Select based on BUILD_TARGET
# ============================================
FROM ${BUILD_TARGET}
