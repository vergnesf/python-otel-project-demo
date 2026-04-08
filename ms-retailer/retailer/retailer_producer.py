import json
import logging
import os
import random
import signal
import sys
import time

from confluent_kafka import KafkaException, Producer
from lib_models.log_formatter import OtelJsonFormatter
from lib_models.models import BeerOrder, BrewStyle
from opentelemetry import metrics, trace
from opentelemetry.propagate import inject
from opentelemetry.trace import SpanKind, StatusCode

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
_handler = logging.StreamHandler()
_handler.setFormatter(OtelJsonFormatter())
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), handlers=[_handler])
logger = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)
beer_orders_created = meter.create_counter("beer_orders.created", description="Number of beer orders produced to Kafka")
beer_orders_failed = meter.create_counter("beer_orders.failed", description="Number of beer orders that failed — simulated (ERROR_RATE) or real Kafka errors")

_RETAILERS = ["Bar du Port", "Brasserie du Centre", "Cave Martin", "Le Zinc", "Bistrot des Halles"]


def delivery_report(err, msg):
    if err is not None:
        logger.error("Message delivery failed: %s", err)
        beer_orders_failed.add(1)
    else:
        logger.info("Message delivered to %s [%d]", msg.topic(), msg.partition())


_kafka_bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_kafka_server_address = _kafka_bootstrap.split(",")[0].split(":")[0]
producer = Producer({"bootstrap.servers": _kafka_bootstrap})


def send_beer_order(beer_order: BeerOrder):
    headers: dict[str, str] = {}
    inject(headers)
    producer.produce("beer-orders", value=json.dumps(beer_order.model_dump()), headers=list(headers.items()), callback=delivery_report)
    producer.poll(0)


def _run_once(error_rate: float) -> None:
    with tracer.start_as_current_span("send beer-order", kind=SpanKind.PRODUCER) as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.operation.name", "send")
        span.set_attribute("messaging.operation.type", "publish")
        span.set_attribute("messaging.destination.name", "beer-orders")
        span.set_attribute("server.address", _kafka_server_address)
        if random.random() < error_rate:
            exc = RuntimeError("simulated failure")
            span.set_status(StatusCode.ERROR, "simulated failure (ERROR_RATE)")
            span.record_exception(exc)
            span.set_attribute("error.type", type(exc).__name__)
            logger.error("failed to send beer order (Kafka/network failure)")
            beer_orders_failed.add(1)
        else:
            beer_order = BeerOrder(
                brew_style=random.choice(list(BrewStyle)),
                quantity=random.randint(1, 20),
                retailer_name=random.choice(_RETAILERS),
            )
            span.set_attribute("retailer.name", beer_order.retailer_name)
            span.set_attribute("brew.style", beer_order.brew_style.value)
            logger.info("Created beer order: %s", beer_order.model_dump())
            try:
                send_beer_order(beer_order)
                logger.info("Beer order sent successfully: %s", beer_order.model_dump())
                beer_orders_created.add(1, {"brew_style": beer_order.brew_style.value, "retailer_name": beer_order.retailer_name})
            except (KafkaException, BufferError) as exc:
                span.set_status(StatusCode.ERROR, str(exc))
                span.record_exception(exc)
                span.set_attribute("error.type", type(exc).__name__)
                logger.error("failed to enqueue beer order: %s", exc)
                beer_orders_failed.add(1)


if __name__ == "__main__":
    if not os.environ.get("KAFKA_BOOTSTRAP_SERVERS"):
        logger.error("KAFKA_BOOTSTRAP_SERVERS is not set — cannot connect to Kafka. Exiting.")
        sys.exit(1)
    try:
        interval_seconds = int(os.getenv("INTERVAL_SECONDS", "10"))
    except ValueError:
        logger.error("Invalid INTERVAL_SECONDS value, must be an integer. Using default 10.")
        interval_seconds = 10
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
        "Retailer service starting with ERROR_RATE=%s and INTERVAL_SECONDS=%s",
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
