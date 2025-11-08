# Use an official Python base image
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

USER root

# Enable Python 3.14 JIT compiler for performance optimization
ENV PYTHON_JIT=1

# Install Node.js and unzip (required for Reflex)
RUN apt-get update && \
    apt-get install -y curl unzip && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy only dependency files first (for better layer caching)
COPY agents-ui/pyproject.toml /app/pyproject.toml
COPY common/common/ /app/common/common

# Install uv and dependencies (excluding dev dependencies)
# This layer will be cached unless dependencies change
RUN pip install uv && \
    ```dockerfile
    ARG DOCKER_REGISTRY=""
    ARG IMG_PYTHON="python:3.14-slim"

    # ============================================
    # Builder stage: install deps and build frontend
    # ============================================
    FROM ${DOCKER_REGISTRY}${IMG_PYTHON} AS builder

    WORKDIR /app

    # Install Node.js (needed for Reflex frontend build)
    RUN apt-get update && \
        apt-get install -y curl unzip && \
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
        apt-get install -y nodejs && \
        rm -rf /var/lib/apt/lists/*

    # Copy dependency files for caching
    COPY agents-ui/pyproject.toml /app/pyproject.toml
    COPY common/common/ /app/common/common

    # Install uv and Python dependencies into a venv
    RUN pip install --no-cache-dir uv && \
        uv sync --no-dev

    # Copy app code and Reflex config
    COPY agents-ui/agents_ui /app/agents_ui
    COPY agents-ui/rxconfig.py /app/rxconfig.py

    # Initialize Reflex (install frontend deps and build)
    # Use uv run reflex init to prepare static assets
    RUN uv run reflex init

    # ============================================
    # Runtime stage: slim image with venv and app
    # ============================================
    FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

    USER root

    # Enable Python JIT for performance parity
    ENV PYTHON_JIT=1

    WORKDIR /app

    # Copy venv and common libs from builder
    COPY --from=builder /app/.venv /app/.venv
    COPY --from=builder /app/common /app/common

    # Copy application code and Reflex built assets
    COPY --from=builder /app/agents_ui /app/agents_ui
    COPY --from=builder /app/rxconfig.py /app/rxconfig.py

    # Ensure venv is used
    ENV PATH="/app/.venv/bin:$PATH"

    EXPOSE 3002
    EXPOSE 8000

    # Default command runs the Reflex server (frontend + backend)
    CMD ["uv", "run", "reflex", "run", "--env", "prod", "--loglevel", "info"]

    ```
