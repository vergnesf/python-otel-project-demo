# Multi-stage build for minimal image size
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"

# ============================================
# Builder stage: Install dependencies
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON} AS builder

WORKDIR /app

# Copy dependency files
COPY agent-metrics/pyproject.toml /app/pyproject.toml
COPY common-ai/common_ai/ /app/common-ai/common_ai
COPY common-ai/pyproject.toml /app/common-ai/pyproject.toml

# Install uv and dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev && \
    
    uv pip install -e /app/common-ai

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
COPY --from=builder /app/common-ai /app/common-ai

# Copy application code
COPY agent-metrics/agent_metrics /app/agent_metrics

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

EXPOSE 8003

# Set the default command to run the metrics agent
CMD ["uvicorn", "agent_metrics.main:app", "--host", "0.0.0.0", "--port", "8003"]
