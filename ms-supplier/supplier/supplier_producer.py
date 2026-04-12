import json
import logging
import os
import random
import signal
import sys
import time

from confluent_kafka import Producer
from lib_models.log_formatter import OtelJsonFormatter
from lib_models.models import IngredientStock, IngredientType
from opentelemetry import metrics, trace
from opentelemetry.propagate import inject
from opentelemetry.trace import SpanKind, StatusCode

# Configure the logger with environment variable
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
_handler = logging.StreamHandler()
_handler.setFormatter(OtelJsonFormatter())
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), handlers=[_handler])
logger = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)
# Note: ingredient_deliveries_created counts messages handed to the Kafka client buffer,
# not broker-confirmed deliveries. Broker delivery failures are logged via delivery_report callback.
ingredient_deliveries_created = meter.create_counter("ingredient_deliveries.created", description="Number of ingredient deliveries produced to Kafka")
ingredient_deliveries_failed = meter.create_counter("ingredient_deliveries.failed", description="Number of ingredient deliveries dropped due to ERROR_RATE")


# Kafka delivery report callback
def delivery_report(err, msg):
    if err is not None:
        logger.error("Message delivery failed: %s", err)
    else:
        logger.info("Message delivered to %s [%d]", msg.topic(), msg.partition())


# Initialize the Kafka producer
_kafka_bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_kafka_server_address = _kafka_bootstrap.split(",")[0].split(":")[0]
producer = Producer({"bootstrap.servers": _kafka_bootstrap})


def send_ingredient(ingredient: IngredientStock):
    headers: dict[str, str] = {}
    inject(headers)  # inject W3C traceparent/tracestate from active span
    producer.produce("ingredient-deliveries", value=json.dumps(ingredient.model_dump()), headers=list(headers.items()), callback=delivery_report)
    producer.poll(0)


def _run_once(error_rate: float) -> None:
    # Simulate random error for observability testing
    # The error rate is controlled by the ERROR_RATE environment variable (default: 0.1)
    # Span name follows OTEL messaging semconv: "{operation} {destination}"
    with tracer.start_as_current_span("send ingredient-deliveries", kind=SpanKind.PRODUCER) as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.operation.name", "send")
        span.set_attribute("messaging.operation.type", "publish")
        span.set_attribute("messaging.destination.name", "ingredient-deliveries")
        span.set_attribute("server.address", _kafka_server_address)
        if random.random() < error_rate:
            exc = RuntimeError("simulated failure")
            span.set_status(StatusCode.ERROR, "simulated failure (ERROR_RATE)")
            span.record_exception(exc)
            span.set_attribute("error.type", type(exc).__name__)
            logger.error("failed to send ingredient delivery (Kafka/network failure)")
            ingredient_deliveries_failed.add(1)
        else:
            ingredient = IngredientStock(
                ingredient_type=random.choice(list(IngredientType)),
                quantity=random.randint(1, 100),
            )
            logger.info("Created ingredient delivery: %s", ingredient.model_dump())
            send_ingredient(ingredient)
            logger.info("Ingredient delivery sent successfully: %s", ingredient.model_dump())
            ingredient_deliveries_created.add(1, {"ingredient_type": ingredient.ingredient_type.value})


if __name__ == "__main__":
    if not os.environ.get("KAFKA_BOOTSTRAP_SERVERS"):
        logger.error("KAFKA_BOOTSTRAP_SERVERS is not set — cannot connect to Kafka. Exiting.")
        sys.exit(1)
    try:
        interval_seconds = int(os.getenv("INTERVAL_SECONDS", "60"))
    except ValueError:
        logger.error("Invalid INTERVAL_SECONDS value, must be an integer. Using default 60.")
        interval_seconds = 60
    if interval_seconds < 1:
        logger.warning("INTERVAL_SECONDS=%d is less than 1 — clamping to 1 to avoid busy-loop", interval_seconds)
        interval_seconds = 1
    try:
        ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))
    except ValueError:
        logger.error("Invalid ERROR_RATE value, must be a float. Using default 0.1.")
        ERROR_RATE = 0.1
    if not 0.0 <= ERROR_RATE <= 1.0:
        logger.warning("ERROR_RATE=%.2f is outside [0.0, 1.0] — clamping", ERROR_RATE)
        ERROR_RATE = max(0.0, min(1.0, ERROR_RATE))

    logger.info(
        "Supplier service starting with ERROR_RATE=%s and INTERVAL_SECONDS=%s",
        ERROR_RATE,
        interval_seconds,
    )

    running = True

    def _shutdown(signum, frame):
        global running
        logger.info("Received signal %s, shutting down", signum)
        running = False

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        while running:
            _run_once(ERROR_RATE)
            time.sleep(interval_seconds)
    finally:
        logger.info("Flushing producer before exit")
        producer.flush()
