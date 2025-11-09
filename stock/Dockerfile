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

COPY stock/pyproject.toml /app/stock/
COPY common-models /app/common-models/

RUN pip install --no-cache-dir uv && \
    uv add pip && \
    uv run --no-dev opentelemetry-bootstrap -a install

COPY stock/stock /app/stock/stock/


CMD ["uv", "run", "--no-dev", "opentelemetry-instrument", "python", "stock/main.py"]

# ============================================
# Prod stage: Optimized production image
# ============================================
FROM base AS prod

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY stock/pyproject.toml /app/stock/
COPY common-models /app/common-models/

RUN pip install --no-cache-dir uv && \
    uv add pip && \
    uv run --no-dev opentelemetry-bootstrap -a install

COPY stock/stock /app/stock/stock/

RUN chown -R appuser:appuser /app

USER appuser


CMD ["uv", "run", "--no-dev", "opentelemetry-instrument", "python", "stock/main.py"]

# ============================================
# Final stage: Select based on BUILD_TARGET
# ============================================
FROM ${BUILD_TARGET}
