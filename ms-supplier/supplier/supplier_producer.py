import json
import logging
import os
import random
import signal
import time

from confluent_kafka import Producer
from lib_models.models import Stock, WoodType
from opentelemetry import trace
from opentelemetry.trace import StatusCode

# Configure the logger with environment variable
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(name)s %(levelname)s [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, log_level, logging.INFO))

tracer = trace.get_tracer(__name__)


# Kafka delivery report callback
def delivery_report(err, msg):
    if err is not None:
        logger.error("Message delivery failed: %s", err)
    else:
        logger.info("Message delivered to %s [%d]", msg.topic(), msg.partition())


# Initialize the Kafka producer
producer = Producer({"bootstrap.servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")})


def send_stock(stock: Stock):
    producer.produce("stocks", value=json.dumps(stock.model_dump()), callback=delivery_report)
    producer.poll(0)


def _run_once(error_rate: float) -> None:
    # Simulate random error for observability testing
    # The error rate is controlled by the ERROR_RATE environment variable (default: 0.1)
    with tracer.start_as_current_span("send_stock") as span:
        if random.random() < error_rate:
            span.set_status(StatusCode.ERROR, "simulated failure (ERROR_RATE)")
            span.record_exception(RuntimeError("simulated failure"))
            logger.error("failed to send stock (Kafka/network failure)")
        else:
            stock = Stock(
                wood_type=random.choice(list(WoodType)),
                quantity=random.randint(1, 100),
            )
            logger.info("Created stock: %s", stock.model_dump())
            send_stock(stock)
            logger.info("Stock sent successfully: %s", stock.model_dump())


if __name__ == "__main__":
    interval_seconds = int(os.getenv("INTERVAL_SECONDS", 60))
    ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))

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
