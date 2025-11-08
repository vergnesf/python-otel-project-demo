# Use an official Python base image
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

USER root

# Enable Python 3.14 JIT compiler for performance optimization
ENV PYTHON_JIT=1

# Set the working directory
WORKDIR /app

# Copy only dependency files first (for better layer caching)
COPY agent-orchestrator/pyproject.toml /app/pyproject.toml
COPY common/common/ /app/common/common

# Install uv and dependencies (excluding dev dependencies)
# This layer will be cached unless dependencies change
RUN pip install uv && \
    uv sync --no-dev

# Copy application code (invalidates cache only when code changes)
COPY agent-orchestrator/agent_orchestrator /app/agent_orchestrator

EXPOSE 8001

# Set the default command to run the orchestrator
CMD ["uv", "run", "uvicorn", "agent_orchestrator.main:app", "--host", "0.0.0.0", "--port", "8001"]
