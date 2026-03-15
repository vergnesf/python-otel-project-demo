import json
import logging
import os
import random
import time

import requests
from confluent_kafka import Consumer, KafkaError, KafkaException
from lib_models.logging import OtelJsonFormatter
from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.trace import SpanKind, StatusCode

# Configure the logger with environment variable
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
_handler = logging.StreamHandler()
_handler.setFormatter(OtelJsonFormatter())
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), handlers=[_handler])
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, log_level, logging.INFO))

tracer = trace.get_tracer(__name__)

# Initialize the Kafka consumer
consumer = Consumer(
    {
        "bootstrap.servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        "group.id": "stock-check-group",
        "auto.offset.reset": "earliest",
    }
)

consumer.subscribe(["stocks"])

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000") + "/stocks"


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
    with tracer.start_as_current_span("process stocks", links=links, kind=SpanKind.CONSUMER) as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.operation.name", "process")
        span.set_attribute("messaging.operation.type", "process")
        span.set_attribute("messaging.destination.name", "stocks")
        span.set_attribute("messaging.consumer.group.name", "stock-check-group")
        # Simulate random error for observability testing
        # The error rate is controlled by the ERROR_RATE environment variable (default: 0.1)
        if random.random() < error_rate:
            exc = RuntimeError("simulated failure")
            span.set_status(StatusCode.ERROR, "simulated failure (ERROR_RATE)")
            span.record_exception(exc)
            span.set_attribute("error.type", type(exc).__name__)
            logger.error("failed to process stock (API or network failure)")
            return

        stock_data = json.loads(msg.value().decode("utf-8"))
        logger.info("Received stock data: %s", stock_data)

        try:
            response = requests.post(API_URL, json=stock_data, timeout=5)
            if response.status_code == 201:
                logger.info("Stock data successfully sent to API")
            else:
                logger.error("Failed to send stock data to API: %s", response.text)
        except requests.Timeout:
            logger.error("Timeout calling API %s, skipping message", API_URL)
        except requests.RequestException as e:
            logger.error("HTTP error calling API: %s", e)


def consume_messages():
    try:
        ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))
        logger.info("Starting message consumption loop with ERROR_RATE=%s", ERROR_RATE)

        while True:
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
    logger.info("SupplierCheck service starting")
    consume_messages()
