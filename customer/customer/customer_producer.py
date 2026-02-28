import json
import logging
import os
import random
import time

from common_models.models import Order, WoodType
from confluent_kafka import Producer

# Configure the logger with environment variable
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, log_level, logging.INFO))


# Kafka delivery report callback
def delivery_report(err, msg):
    if err is not None:
        logger.error("Message delivery failed: %s", err)
    else:
        logger.info("Message delivered to %s [%d]", msg.topic(), msg.partition())


# Initialize the Kafka producer
producer = Producer(
    {"bootstrap.servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")}
)


def send_order(order: Order):
    producer.produce(
        "orders", value=json.dumps(order.model_dump()), callback=delivery_report
    )
    producer.poll(0)


if __name__ == "__main__":
    interval_seconds = os.getenv("INTERVAL_SECONDS", "60")
    ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))

    logger.info(
        "Customer service starting with ERROR_RATE=%s and INTERVAL_SECONDS=%s",
        ERROR_RATE,
        interval_seconds,
    )

    while True:
        # Simulate random error for observability testing
        # The error rate is controlled by the ERROR_RATE environment variable (default: 0.1)
        if random.random() < ERROR_RATE:
            logger.error("failed to send order (Kafka/network failure)")
            time.sleep(int(interval_seconds))
            continue

        order = Order(
            wood_type=random.choice(list(WoodType)),
            quantity=random.randint(1, 100),
        )
        logger.info("Created order: %s", order.model_dump())

        send_order(order)
        logger.info("Order sent successfully: %s", order.model_dump())
        time.sleep(int(interval_seconds))

    # Wait for any outstanding messages to be delivered and delivery reports to be received
    producer.flush()
