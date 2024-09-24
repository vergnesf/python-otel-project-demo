# Use an official Python base image
ARG DOCKER_REGISTRY
ARG IMG_PYTHON
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

USER root

# Set the working directory
WORKDIR /app

# Copy Poetry configuration files
COPY ordercheck/pyproject.toml /app/
COPY ordercheck/poetry.lock  /app/
COPY ordercheck/ordercheck /app
COPY common/common/ /app/common/common

# Install Poetry
RUN pip install poetry && \
    poetry install --no-root && \
    poetry run opentelemetry-bootstrap -a install

# Set the default command to run the producer
CMD ["poetry", "run", "opentelemetry-instrument", "python", "/app/ordercheck_consumer.py"]