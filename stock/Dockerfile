# Multi-stage build for minimal image size
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"

# ============================================
# Build stage: Install dependencies
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON} AS builder

WORKDIR /app/stock

# Copy dependency files from root context
COPY stock/pyproject.toml ./pyproject.toml
COPY common-models ../common-models

# Install uv and dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev && \
    uv run --no-dev opentelemetry-bootstrap -a install

# ============================================
# Runtime stage: Minimal runtime image
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

WORKDIR /app/stock

# Copy venv from builder
COPY --from=builder /app/stock/.venv .venv
COPY --from=builder /app/common-models ../common-models

# Copy application code
COPY stock/stock ../stock

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set PATH to use venv
ENV PATH="/app/stock/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Set the default command
CMD ["opentelemetry-instrument", "python", "/app/stock/main.py"]
