# Use an official Python base image
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.13-slim"
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

USER root

# Set the working directory
WORKDIR /app

# Copy uv configuration files
COPY agent-logs/pyproject.toml /app/
COPY agent-logs/agent_logs /app/agent_logs
COPY agents-common/agents_common/ /app/agents_common

# Install uv
RUN pip install uv && \
    uv add pip

EXPOSE 8002

# Set the default command to run the logs agent
CMD ["uv", "run", "uvicorn", "agent_logs.main:app", "--host", "0.0.0.0", "--port", "8002"]
