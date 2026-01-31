# Build arguments for cache busting
FROM python:3.14-slim

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHON_JIT=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/agent-ui

# Copy and install dependencies
COPY agent-ui/pyproject.toml ./
COPY agent-ui/uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv add pip

# Copy application code
COPY agent-ui/agent_ui ./agent_ui/

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "uvicorn", "agent_ui.main:app", "--host", "0.0.0.0", "--port", "8000"]