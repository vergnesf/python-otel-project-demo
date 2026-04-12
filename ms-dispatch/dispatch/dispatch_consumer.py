import json
import logging
import os
import random
import signal
import sys
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
beer_orders_dispatched = meter.create_counter("beer_orders.dispatched", description="Beer orders successfully shipped via ms-beerstock")
beer_orders_backorder = meter.create_counter("beer_orders.backorder", description="Beer orders in backorder (insufficient stock in ms-beerstock)")
beer_orders_errors = meter.create_counter("beer_orders.dispatch_errors", description="Beer orders with processing errors during dispatch")

# Initialize the Kafka consumer
_kafka_bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_kafka_server_address = _kafka_bootstrap.split(",")[0].split(":")[0]
consumer = Consumer(
    {
        "bootstrap.servers": _kafka_bootstrap,
        "group.id": "dispatch-group",
        "auto.offset.reset": "earliest",
    }
)

API_URL_BEERSTOCK = os.environ.get("API_URL_BEERSTOCK", "http://ms-beerstock:5002") + "/beerstock/ship"


def _process_message(msg, error_rate: float) -> None:
    # Extract W3C trace context from Kafka message headers and attach it as a span link.
    # OTEL messaging spec recommends links (not parent-child) as the default for messaging:
    # https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/
    raw_headers = msg.headers() or []
    carrier = {k: v.decode() if isinstance(v, bytes) else v for k, v in raw_headers}
    remote_ctx = extract(carrier)
    remote_span_ctx = trace.get_current_span(remote_ctx).get_span_context()
    links = [trace.Link(remote_span_ctx)] if remote_span_ctx.is_valid else []

    with tracer.start_as_current_span("process beer-orders", links=links, kind=SpanKind.CONSUMER) as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.operation.name", "process")
        span.set_attribute("messaging.operation.type", "process")
        span.set_attribute("messaging.destination.name", "beer-orders")
        span.set_attribute("messaging.consumer.group.name", "dispatch-group")
        span.set_attribute("server.address", _kafka_server_address)
        span.set_attribute("messaging.kafka.message.offset", msg.offset())

        if random.random() < error_rate:
            exc = RuntimeError("simulated failure")
            span.set_status(StatusCode.ERROR, "simulated failure (ERROR_RATE)")
            span.record_exception(exc)
            span.set_attribute("error.type", type(exc).__name__)
            logger.error("failed to process beer-orders message (ERROR_RATE)")
            beer_orders_errors.add(1)
            return

        try:
            beer_order_data = json.loads(msg.value().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            span.set_status(StatusCode.ERROR, "malformed message")
            span.record_exception(e)
            span.set_attribute("error.type", type(e).__name__)
            logger.error("Skipping malformed Kafka message: %s", e)
            beer_orders_errors.add(1)
            return

        brew_style = beer_order_data.get("brew_style", "unknown")
        quantity = beer_order_data.get("quantity", 0)
        retailer_name = beer_order_data.get("retailer_name", "unknown")

        span.set_attribute("retailer.name", retailer_name)

        logger.info("Received beer order: brew_style=%s quantity=%d retailer=%s", brew_style, quantity, retailer_name)

        try:
            response = requests.post(
                API_URL_BEERSTOCK,
                json={"brew_style": brew_style, "quantity": quantity},
                timeout=5,
            )
            if response.status_code == 200:
                span.set_attribute("dispatch.status", "shipped")
                logger.info("Shipment confirmed: brew_style=%s quantity=%d retailer=%s", brew_style, quantity, retailer_name)
                beer_orders_dispatched.add(1, {"brew_style": brew_style})
            elif response.status_code == 400:
                span.set_attribute("dispatch.status", "backorder")
                logger.warning("Backorder: insufficient stock for brew_style=%s quantity=%d retailer=%s", brew_style, quantity, retailer_name)
                beer_orders_backorder.add(1, {"brew_style": brew_style})
            else:
                span.set_status(StatusCode.ERROR, f"unexpected HTTP {response.status_code}")
                span.set_attribute("error.type", "HTTPError")
                logger.error("Unexpected response from ms-beerstock: status=%d body=%s", response.status_code, response.text)
                beer_orders_errors.add(1)
        except requests.Timeout:
            span.set_status(StatusCode.ERROR, "timeout")
            span.set_attribute("error.type", "Timeout")
            logger.error("Timeout calling ms-beerstock for brew_style=%s, skipping message", brew_style)
            beer_orders_errors.add(1)
        except requests.RequestException as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            span.set_attribute("error.type", type(e).__name__)
            logger.error("HTTP error calling ms-beerstock: %s", e)
            beer_orders_errors.add(1)


running = True


def _shutdown(signum, frame):
    global running
    logger.info("Received signal %s, shutting down", signum)
    running = False


def consume_messages():
    consumer.subscribe(["beer-orders"])
    try:
        ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))
    except ValueError:
        logger.error("Invalid ERROR_RATE value, must be a float. Using default 0.1.")
        ERROR_RATE = 0.1
    if not 0.0 <= ERROR_RATE <= 1.0:
        logger.warning("ERROR_RATE=%.2f is outside [0.0, 1.0] — clamping", ERROR_RATE)
        ERROR_RATE = max(0.0, min(1.0, ERROR_RATE))
    logger.info("Starting dispatch message consumption loop with ERROR_RATE=%s", ERROR_RATE)

    try:
        while running:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            err = msg.error()
            if err:
                if err.code() == KafkaError._PARTITION_EOF:
                    logger.info(
                        "End of partition reached %s [%d] at offset %d",
                        msg.topic(),
                        msg.partition(),
                        msg.offset(),
                    )
                elif err.code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    logger.warning("Topic not available yet, retrying in 5s...")
                    time.sleep(5)
                else:
                    raise KafkaException(err)
            else:
                _process_message(msg, ERROR_RATE)
    except KeyboardInterrupt:
        logger.info("Consumer shutting down due to keyboard interrupt")
    finally:
        consumer.close()
        logger.info("Consumer closed")


if __name__ == "__main__":
    if not os.environ.get("KAFKA_BOOTSTRAP_SERVERS"):
        logger.error("KAFKA_BOOTSTRAP_SERVERS is not set — cannot connect to Kafka. Exiting.")
        sys.exit(1)
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    logger.info("Dispatch service starting")
    consume_messages()
