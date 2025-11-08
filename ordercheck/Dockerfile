# Multi-stage build for minimal image size
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"

# ============================================
# Builder stage: Install dependencies
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON} AS builder

WORKDIR /app

# Copy dependency files
COPY ordercheck/pyproject.toml /app/pyproject.toml
COPY common-models/pyproject.toml /app/common-models/pyproject.toml
COPY common-models/common_models/ /app/common-models/common_models

# Install uv and dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev && \
    uv pip install -e /app/common-models && \
    uv run opentelemetry-bootstrap -a install

# ============================================
# Runtime stage: Minimal image
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

# Update OS packages
RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser -m

# Enable Python 3.14 JIT compiler for performance optimization
ENV PYTHON_JIT=1

WORKDIR /app

# Copy only the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/common-models /app/common-models

# Copy application code
COPY ordercheck/ordercheck /app

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Set the default command to run the consumer
CMD ["opentelemetry-instrument", "python", "/app/ordercheck_consumer.py"]