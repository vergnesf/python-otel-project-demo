# Single-stage build - simpler and avoids shebang issues
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"

FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

# Update OS packages
RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser -m

# Enable Python 3.14 JIT compiler for performance optimization
ENV PYTHON_JIT=1

WORKDIR /app/agent-logs

# Copy dependency files from root context
COPY agent-logs/pyproject.toml ./pyproject.toml
COPY common-ai ../common-ai

# Install uv and dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev

# Copy application code
COPY agent-logs/agent_logs ../agent_logs

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set PATH to use venv
ENV PATH="/app/agent-logs/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

EXPOSE 8002

# Set the default command
CMD ["uv", "run", "uvicorn", "agent_logs.main:app", "--host", "0.0.0.0", "--port", "8002"]
