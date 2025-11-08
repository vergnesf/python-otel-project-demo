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

WORKDIR /app/agent-traces

# Copy dependency files from root context
COPY agent-traces/pyproject.toml ./pyproject.toml
COPY common-ai ../common-ai

# Install uv and dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev

# Copy application code
COPY agent-traces/agent_traces ../agent_traces

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set PATH to use venv
ENV PATH="/app/agent-traces/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

EXPOSE 8004

# Set the default command
CMD ["uv", "run", "uvicorn", "agent_traces.main:app", "--host", "0.0.0.0", "--port", "8004"]
