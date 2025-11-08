# Use an official Python base image
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.13-slim"
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

USER root

# Install Node.js (required for Reflex)
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy uv configuration files
COPY agents-ui/pyproject.toml /app/
COPY agents-ui/agents_ui /app/agents_ui
COPY agents-ui/rxconfig.py /app/
COPY agents-common/agents_common/ /app/agents_common

# Install uv and dependencies
RUN pip install uv && \
    uv add pip

# Initialize Reflex (downloads frontend dependencies)
RUN uv run reflex init

EXPOSE 3002
EXPOSE 8000

# Set the default command to run the UI
CMD ["uv", "run", "reflex", "run", "--env", "prod", "--loglevel", "info"]
