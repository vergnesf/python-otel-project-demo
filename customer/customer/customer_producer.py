import json
import logging
import os
import random
import time

from confluent_kafka import Producer

from common.common.models import Order, WoodType

# Configure the logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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

    while True:
        order = Order(
            wood_type=random.choice(list(WoodType)),
            quantity=random.randint(1, 100),
        )
        send_order(order)
        logger.info("Order sent: %s", order.model_dump())
        time.sleep(int(interval_seconds))

    # Wait for any outstanding messages to be delivered and delivery reports to be received
    producer.flush()
