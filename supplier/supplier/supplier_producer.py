import json
import logging
import os
import random
import time

from confluent_kafka import Producer

from common.common.models import Stock, WoodType

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


def send_stock(stock: Stock):
    producer.produce("stocks", value=json.dumps(stock.dict()), callback=delivery_report)
    producer.poll(0)


if __name__ == "__main__":
    interval_seconds = int(os.getenv("INTERVAL_SECONDS", 60))

    while True:
        stock = Stock(
            wood_type=random.choice(list(WoodType)),
            quantity=random.randint(1, 100),
        )
        send_stock(stock)
        logger.info("Stock sent: %s", stock.dict())
        time.sleep(interval_seconds)

    # Wait for any outstanding messages to be delivered and delivery reports to be received
    producer.flush()
