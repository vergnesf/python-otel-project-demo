# Multi-stage build for minimal image size
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"

# ============================================
# Build stage: Install dependencies
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON} AS builder

WORKDIR /app/agent-metrics

# Copy dependency files from root context
COPY agent-metrics/pyproject.toml ./pyproject.toml
COPY common-ai ../common-ai

# Install uv and dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev && \
    uv run --no-dev opentelemetry-bootstrap -a requirements > /tmp/otel-requirements.txt && \
    uv pip install -r /tmp/otel-requirements.txt

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

WORKDIR /app/agent-metrics

# Copy venv from builder
COPY --from=builder /app/agent-metrics/.venv .venv
COPY --from=builder /app/common-ai ../common-ai

# Copy application code
COPY agent-metrics/agent_metrics ../agent_metrics

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set PATH to use venv
ENV PATH="/app/agent-metrics/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

EXPOSE 8003

# Set the default command
CMD ["opentelemetry-instrument", "uvicorn", "agent_metrics.main:app", "--host", "0.0.0.0", "--port", "8003"]
