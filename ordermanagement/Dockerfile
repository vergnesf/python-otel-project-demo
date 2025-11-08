# Multi-stage build for minimal image size
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"

# ============================================
# Builder stage: Install dependencies
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON} AS builder

WORKDIR /app

# Copy dependency files
COPY ordermanagement/pyproject.toml /app/pyproject.toml
COPY common/common/ /app/common/common

# Install uv and dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev && \
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
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Enable Python 3.14 JIT compiler for performance optimization
ENV PYTHON_JIT=1

WORKDIR /app

# Copy only the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/common /app/common

# Copy application code
COPY ordermanagement/ordermanagement /app

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH"

# Set the default command to run the service
CMD ["opentelemetry-instrument", "python", "/app/ordermanagement.py"]