# Multi-stage build for minimal image size
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"

# ============================================
# Build stage: Install dependencies
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON} AS builder

WORKDIR /app/customer

# Copy dependency files from root context
COPY customer/pyproject.toml ./pyproject.toml
COPY common-models ../common-models

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

WORKDIR /app/customer

# Copy venv from builder
COPY --from=builder /app/customer/.venv .venv
COPY --from=builder /app/common-models ../common-models

# Copy application code
COPY customer/customer ../customer

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set PATH to use venv
ENV PATH="/app/customer/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Set the default command
CMD ["opentelemetry-instrument", "python", "/app/customer/customer_producer.py"]
