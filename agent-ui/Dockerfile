# Multi-stage build for minimal image size
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"

# ============================================
# Builder stage: install deps and build frontend
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON} AS builder

WORKDIR /app

# Install Node.js and unzip (needed for Reflex frontend build)
RUN apt-get update && \
    apt-get install -y curl unzip && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files for caching
COPY agent-ui/pyproject.toml /app/pyproject.toml

# Install uv and Python dependencies into a venv
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev 

# Copy app code and Reflex config
COPY agent-ui/agent_ui /app/agent_ui
COPY agent-ui/rxconfig.py /app/rxconfig.py

# Initialize Reflex (install frontend deps and build)
RUN uv run --no-dev reflex init

# ============================================
# Runtime stage: slim image with venv and app
# ============================================
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

# Update OS packages and install only Node.js and unzip (for Reflex runtime)
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y ca-certificates curl gnupg unzip && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    apt-get remove -y curl gnupg && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser -m

# Enable Python JIT for performance parity
ENV PYTHON_JIT=1

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code and Reflex built assets
COPY --from=builder /app/agent_ui /app/agent_ui
COPY --from=builder /app/rxconfig.py /app/rxconfig.py
COPY --from=builder /app/.web /app/.web

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Ensure venv is used
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

EXPOSE 3002
EXPOSE 8000

# Default command runs the Reflex server (frontend + backend)
CMD ["reflex", "run", "--env", "prod", "--loglevel", "info"]
