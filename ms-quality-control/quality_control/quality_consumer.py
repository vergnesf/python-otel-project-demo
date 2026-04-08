import json
import logging
import os
import random
import signal
import time

import requests
from confluent_kafka import Consumer, KafkaError, KafkaException
from lib_models.log_formatter import OtelJsonFormatter
from lib_models.models import BrewStatus
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
brews_quality_checked = meter.create_counter("brews.quality_checked", description="Number of brews that passed quality control")
brews_quality_rejected = meter.create_counter("brews.quality_rejected", description="Number of brews that failed quality control")
brews_quality_errors = meter.create_counter("brews.quality_errors", description="Number of brews with processing errors during quality control")

# Initialize the Kafka consumer
_kafka_bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_kafka_server_address = _kafka_bootstrap.split(":")[0]
consumer = Consumer(
    {
        "bootstrap.servers": _kafka_bootstrap,
        "group.id": "quality-control-group",
        "auto.offset.reset": "earliest",
    }
)

API_URL = os.environ.get("API_URL", "http://brewery:5000") + "/brews"

_REJECT_REASONS = ["color_off", "bitterness_high", "clarity_poor"]


def _process_message(msg, reject_rate: float, error_rate: float) -> None:
    # Extract W3C trace context from Kafka message headers and attach it as a span link.
    # OTEL messaging spec recommends links (not parent-child) as the default for messaging.
    raw_headers = msg.headers() or []
    carrier = {k: v.decode() if isinstance(v, bytes) else v for k, v in raw_headers}
    remote_ctx = extract(carrier)
    remote_span_ctx = trace.get_current_span(remote_ctx).get_span_context()
    links = [trace.Link(remote_span_ctx)] if remote_span_ctx.is_valid else []

    with tracer.start_as_current_span("process brews-ready", links=links, kind=SpanKind.CONSUMER) as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.operation.name", "process")
        span.set_attribute("messaging.operation.type", "process")
        span.set_attribute("messaging.destination.name", "brews-ready")
        span.set_attribute("messaging.consumer.group.name", "quality-control-group")
        span.set_attribute("server.address", _kafka_server_address)
        span.set_attribute("messaging.kafka.message.offset", msg.offset())

        # Simulate random processing error
        if random.random() < error_rate:
            exc = RuntimeError("simulated failure")
            span.set_status(StatusCode.ERROR, "simulated failure (ERROR_RATE)")
            span.record_exception(exc)
            span.set_attribute("error.type", type(exc).__name__)
            logger.error("failed to process brews-ready message (ERROR_RATE)")
            brews_quality_errors.add(1)
            return

        try:
            brew_data = json.loads(msg.value().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            span.set_status(StatusCode.ERROR, "malformed message")
            span.record_exception(e)
            span.set_attribute("error.type", type(e).__name__)
            logger.error("Skipping malformed Kafka message: %s", e)
            brews_quality_errors.add(1)
            return

        brew_id = brew_data.get("id")
        brew_style = brew_data.get("brew_style", "unknown")
        logger.info("Quality checking brew %s (style: %s)", brew_id, brew_style)

        # Simulate quality check: pass or fail based on REJECT_RATE
        quality_passed = random.random() >= reject_rate
        span.set_attribute("quality.check.passed", quality_passed)

        if quality_passed:
            new_status = BrewStatus.APPROVED
            span.set_attribute("brew.style", brew_style)
        else:
            reject_reason = random.choice(_REJECT_REASONS)
            new_status = BrewStatus.REJECTED
            span.set_attribute("quality.reject_reason", reject_reason)
            span.set_attribute("brew.style", brew_style)
            logger.warning("Brew %s rejected: %s", brew_id, reject_reason)

        try:
            response = requests.put(f"{API_URL}/{brew_id}", json={"brew_status": new_status.value}, timeout=5)
            if response.status_code == 200:
                if quality_passed:
                    logger.info("Brew %s approved", brew_id)
                    brews_quality_checked.add(1, {"brew_style": brew_style})
                else:
                    brews_quality_rejected.add(1, {"brew_style": brew_style})
            else:
                logger.error("Failed to update brew %s status: %s", brew_id, response.text)
                brews_quality_errors.add(1)
        except requests.Timeout:
            logger.error("Timeout calling API for brew %s, skipping", brew_id)
            brews_quality_errors.add(1)
        except requests.RequestException as e:
            logger.error("HTTP error updating brew %s: %s", brew_id, e)
            brews_quality_errors.add(1)


running = True


def _shutdown(signum, frame):
    global running
    logger.info("Received signal %s, shutting down", signum)
    running = False


def consume_messages():
    consumer.subscribe(["brews-ready"])
    REJECT_RATE = float(os.environ.get("REJECT_RATE", 0.1))
    ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))
    logger.info("Starting quality control loop with REJECT_RATE=%s, ERROR_RATE=%s", REJECT_RATE, ERROR_RATE)

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
                _process_message(msg, REJECT_RATE, ERROR_RATE)
    except KeyboardInterrupt:
        logger.info("Consumer shutting down due to keyboard interrupt")
    finally:
        consumer.close()
        logger.info("Consumer closed")


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    logger.info("Quality control service starting")
    consume_messages()
