# Use an official Python base image
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

USER root

# Set the working directory
WORKDIR /app

# Copy uv configuration files
COPY agent-metrics/pyproject.toml /app/
COPY agent-metrics/agent_metrics /app/agent_metrics
COPY common/common/ /app/common/common

# Install uv and dependencies (excluding dev dependencies)
RUN pip install uv && \
    uv sync --no-dev

EXPOSE 8003

# Set the default command to run the metrics agent
CMD ["uv", "run", "uvicorn", "agent_metrics.main:app", "--host", "0.0.0.0", "--port", "8003"]
