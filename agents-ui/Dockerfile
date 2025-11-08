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
    uv sync --no-dev

# Copy application code and config
COPY agents-ui/agents_ui /app/agents_ui
COPY agents-ui/rxconfig.py /app/rxconfig.py

# Initialize Reflex (downloads frontend dependencies)
RUN uv run reflex init

EXPOSE 3002
EXPOSE 8000

# Set the default command to run the UI
CMD ["uv", "run", "reflex", "run", "--env", "prod", "--loglevel", "info"]
