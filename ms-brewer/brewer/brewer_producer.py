import json
import logging
import os
import random
import signal
import time

from confluent_kafka import Producer
from lib_models.log_formatter import OtelJsonFormatter
from lib_models.models import BrewOrder, BrewStyle, IngredientType
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
# Note: brew_orders_created counts messages handed to the Kafka client buffer (after producer.produce),
# not broker-confirmed deliveries. Broker delivery failures are logged via delivery_report callback.
brew_orders_created = meter.create_counter("brew_orders.created", description="Number of brew orders produced to Kafka")
brew_orders_failed = meter.create_counter("brew_orders.failed", description="Number of brew orders dropped due to ERROR_RATE")


# Kafka delivery report callback
def delivery_report(err, msg):
    if err is not None:
        logger.error("Message delivery failed: %s", err)
    else:
        logger.info("Message delivered to %s [%d]", msg.topic(), msg.partition())


# Initialize the Kafka producer
_kafka_bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_kafka_server_address = _kafka_bootstrap.split(":")[0]
producer = Producer({"bootstrap.servers": _kafka_bootstrap})


def send_brew_order(brew_order: BrewOrder):
    headers: dict[str, str] = {}
    inject(headers)  # inject W3C traceparent/tracestate from active span
    producer.produce("brew-orders", value=json.dumps(brew_order.model_dump()), headers=list(headers.items()), callback=delivery_report)
    producer.poll(0)


def _run_once(error_rate: float) -> None:
    # Simulate random error for observability testing
    # The error rate is controlled by the ERROR_RATE environment variable (default: 0.1)
    # Span name follows OTEL messaging semconv: "{operation} {destination}"
    with tracer.start_as_current_span("send brew-orders", kind=SpanKind.PRODUCER) as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.operation.name", "send")
        span.set_attribute("messaging.operation.type", "publish")
        span.set_attribute("messaging.destination.name", "brew-orders")
        span.set_attribute("server.address", _kafka_server_address)
        if random.random() < error_rate:
            exc = RuntimeError("simulated failure")
            span.set_status(StatusCode.ERROR, "simulated failure (ERROR_RATE)")
            span.record_exception(exc)
            span.set_attribute("error.type", type(exc).__name__)
            logger.error("failed to send brew order (Kafka/network failure)")
            brew_orders_failed.add(1)
        else:
            brew_order = BrewOrder(
                ingredient_type=random.choice(list(IngredientType)),
                quantity=random.randint(1, 100),
                brew_style=random.choice(list(BrewStyle)),
            )
            logger.info("Created brew order: %s", brew_order.model_dump())
            send_brew_order(brew_order)
            logger.info("Brew order sent successfully: %s", brew_order.model_dump())
            brew_orders_created.add(1, {"ingredient_type": brew_order.ingredient_type.value, "brew_style": brew_order.brew_style.value})


if __name__ == "__main__":
    interval_seconds = int(os.getenv("INTERVAL_SECONDS", "60"))
    ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))

    logger.info(
        "Brewer service starting with ERROR_RATE=%s and INTERVAL_SECONDS=%s",
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
