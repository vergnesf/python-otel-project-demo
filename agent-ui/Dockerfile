# Build arguments for cache busting
ARG BUILD_TIMESTAMP
ENV BUILD_TIMESTAMP=${BUILD_TIMESTAMP:-$(date +%s)}

FROM python:3.14-slim

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHON_JIT=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy and install dependencies
COPY pyproject.toml ./

RUN pip install --no-cache-dir uv && \
    uv add pip

# Copy application code
COPY agent_ui ./agent_ui/

# Create a build info file
RUN echo "Build timestamp: ${BUILD_TIMESTAMP}" > /app/BUILD_INFO.txt && \
    echo "Built from: agent-ui" >> /app/BUILD_INFO.txt && \
    echo "Git commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" >> /app/BUILD_INFO.txt

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "agent_ui.main:app", "--host", "0.0.0.0", "--port", "8000"]