# Multi-stage build for minimal image size
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"

# ============================================
# Builder stage: Install dependencies
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON} AS builder

WORKDIR /app

# Copy dependency files
COPY agent-logs/pyproject.toml /app/pyproject.toml
COPY common/common/ /app/common/common

# Install uv and dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev

# ============================================
# Runtime stage: Minimal image
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

USER root

# Enable Python 3.14 JIT compiler for performance optimization
ENV PYTHON_JIT=1

WORKDIR /app

# Copy only the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/common /app/common

# Copy application code
COPY agent-logs/agent_logs /app/agent_logs

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8002

# Set the default command to run the logs agent
CMD ["uvicorn", "agent_logs.main:app", "--host", "0.0.0.0", "--port", "8002"]
