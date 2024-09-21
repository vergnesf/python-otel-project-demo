# Use an official Python base image
ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy Poetry configuration files
COPY customer/pyproject.toml /app/
COPY customer/poetry.lock  /app/
COPY customer/customer /app
COPY common/common/ /app/common/common

# Install Poetry
RUN pip install poetry && \
    poetry install --no-root && \
    poetry run opentelemetry-bootstrap -a install

# Set the default command to run the producer
CMD ["poetry", "run", "opentelemetry-instrument", "python", "/app/customer_producer.py"]
