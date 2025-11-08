# Multi-stage build for minimal image size
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"

# ============================================
# Build stage: Install dependencies
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON} AS builder

WORKDIR /app/agent-orchestrator

# Copy dependency files from root context
COPY agent-orchestrator/pyproject.toml ./pyproject.toml
COPY common-ai ../common-ai

# Install uv and dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev

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

WORKDIR /app/agent-orchestrator

# Copy venv from builder
COPY --from=builder /app/agent-orchestrator/.venv .venv
COPY --from=builder /app/common-ai ../common-ai

# Copy application code
COPY agent-orchestrator/agent_orchestrator ../agent_orchestrator

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set PATH to use venv
ENV PATH="/app/agent-orchestrator/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

EXPOSE 8001

# Set the default command
CMD ["uvicorn", "agent_orchestrator.main:app", "--host", "0.0.0.0", "--port", "8001"]
