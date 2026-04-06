import json
import logging
import os
import random
import signal
import time

import requests
from confluent_kafka import Consumer, KafkaError, KafkaException
from lib_models.log_formatter import OtelJsonFormatter
from opentelemetry import metrics, trace
from opentelemetry.propagate import extract
from opentelemetry.trace import SpanKind, StatusCode

# Configure the logger with environment variable
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
_handler = logging.StreamHandler()
_handler.setFormatter(OtelJsonFormatter())
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), handlers=[_handler])
logger = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)
brew_orders_processed = meter.create_counter("brew_orders.processed", description="Number of brew orders successfully forwarded to ms-brewery")
brew_orders_processing_errors = meter.create_counter("brew_orders.processing_errors", description="Number of brew orders failed (HTTP error or ERROR_RATE)")

# Initialize the Kafka consumer
_kafka_bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
if not _kafka_bootstrap:
    logger.warning("KAFKA_BOOTSTRAP_SERVERS is empty — server.address span attribute will be empty")
_kafka_server_address = _kafka_bootstrap.split(",")[0].split(":")[0]
consumer = Consumer(
    {
        "bootstrap.servers": _kafka_bootstrap,
        "group.id": "brew-check-group",
        "auto.offset.reset": "earliest",
    }
)

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000") + "/brews"


def _process_message(msg, error_rate: float) -> None:
    # Extract W3C trace context from Kafka message headers and attach it as a span link.
    # OTEL messaging spec recommends links (not parent-child) as the default for messaging:
    # https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/
    raw_headers = msg.headers() or []
    carrier = {k: v.decode() if isinstance(v, bytes) else v for k, v in raw_headers}
    remote_ctx = extract(carrier)
    remote_span_ctx = trace.get_current_span(remote_ctx).get_span_context()
    links = [trace.Link(remote_span_ctx)] if remote_span_ctx.is_valid else []

    # Span name follows OTEL messaging semconv: "{operation} {destination}"
    with tracer.start_as_current_span("process brew-orders", links=links, kind=SpanKind.CONSUMER) as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.operation.name", "process")
        span.set_attribute("messaging.operation.type", "process")
        span.set_attribute("messaging.destination.name", "brew-orders")
        span.set_attribute("messaging.consumer.group.name", "brew-check-group")
        span.set_attribute("server.address", _kafka_server_address)
        span.set_attribute("messaging.kafka.message.offset", msg.offset())
        # Simulate random error for observability testing
        # The error rate is controlled by the ERROR_RATE environment variable (default: 0.1)
        if random.random() < error_rate:
            exc = RuntimeError("simulated failure")
            span.set_status(StatusCode.ERROR, "simulated failure (ERROR_RATE)")
            span.record_exception(exc)
            span.set_attribute("error.type", type(exc).__name__)
            logger.error("failed to process brew order (API or network failure)")
            brew_orders_processing_errors.add(1)
            return

        try:
            brew_order_data = json.loads(msg.value().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            span.set_status(StatusCode.ERROR, "malformed message")
            span.record_exception(e)
            span.set_attribute("error.type", type(e).__name__)
            logger.error("Skipping malformed Kafka message: %s", e)
            brew_orders_processing_errors.add(1)
            return

        logger.info("Received brew order data: %s", brew_order_data)

        try:
            response = requests.post(API_URL, json=brew_order_data, timeout=5)
            if response.status_code == 201:
                logger.info("Brew order data successfully sent to API")
                brew_orders_processed.add(1)
            else:
                logger.error("Failed to send brew order data to API: %s", response.text)
                brew_orders_processing_errors.add(1)
        except requests.Timeout:
            logger.error("Timeout calling API %s, skipping message", API_URL)
            brew_orders_processing_errors.add(1)
        except requests.RequestException as e:
            logger.error("HTTP error calling API: %s", e)
            brew_orders_processing_errors.add(1)


running = True


def _shutdown(signum, frame):
    global running
    logger.info("Received signal %s, shutting down", signum)
    running = False


def consume_messages():
    consumer.subscribe(["brew-orders"])
    ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))
    if not 0.0 <= ERROR_RATE <= 1.0:
        logger.warning("ERROR_RATE=%.2f is outside [0.0, 1.0] — clamping", ERROR_RATE)
        ERROR_RATE = max(0.0, min(1.0, ERROR_RATE))
    logger.info("Starting message consumption loop with ERROR_RATE=%s", ERROR_RATE)

    try:
        while running:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.info(
                        "End of partition reached %s [%d] at offset %d",
                        msg.topic(),
                        msg.partition(),
                        msg.offset(),
                    )
                elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    logger.warning("Topic not available yet, retrying in 5s...")
                    time.sleep(5)
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                _process_message(msg, ERROR_RATE)
    except KeyboardInterrupt:
        logger.info("Consumer shutting down due to keyboard interrupt")
    finally:
        consumer.close()
        logger.info("Consumer closed")


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    logger.info("BrewCheck service starting")
    consume_messages()
