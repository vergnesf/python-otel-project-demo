# Use an official Python base image
ARG DOCKER_REGISTRY
ARG IMG_PYTHON
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

USER root

# Set the working directory
WORKDIR /app

# Copy Poetry configuration files
COPY stock/pyproject.toml /app/
COPY stock/poetry.lock  /app/
COPY stock/stock /app/stock
COPY common/common/ /app/common/common

# Install Poetry
RUN pip install poetry && \
    poetry install --no-root && \
    poetry run opentelemetry-bootstrap -a install

EXPOSE 5000

# Set the default command to run the producer
CMD ["poetry", "run", "opentelemetry-instrument", "python", "-m", "stock.main"]


