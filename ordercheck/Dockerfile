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

COPY ordercheck/pyproject.toml /app/ordercheck/
COPY common-models /app/common-models/

WORKDIR /app/ordercheck

RUN pip install --no-cache-dir uv && \
    uv add pip && \
    uv run --no-dev opentelemetry-bootstrap -a install

COPY ordercheck/ordercheck /app/ordercheck/ordercheck/


CMD ["uv", "run", "--no-dev", "opentelemetry-instrument", "python", "ordercheck/ordercheck_consumer.py"]

# ============================================
# Prod stage: Optimized production image
# ============================================
FROM base AS prod

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY ordercheck/pyproject.toml ./ordercheck/
COPY common-models ./common-models/

WORKDIR /app/ordercheck

RUN pip install --no-cache-dir uv && \
    uv sync --directory ordercheck --no-dev && \
    uv run --directory ordercheck --no-dev opentelemetry-bootstrap -a install

COPY ordercheck/ordercheck /app/ordercheck/ordercheck/

RUN chown -R appuser:appuser /app

USER appuser


CMD ["uv", "run", "--directory", "ordercheck", "opentelemetry-instrument", "python", "ordercheck/ordercheck_consumer.py"]

# ============================================
# Final stage: Select based on BUILD_TARGET
# ============================================
FROM ${BUILD_TARGET}
