import random
import json
import logging
import os

import requests
from confluent_kafka import Consumer, KafkaError, KafkaException

# Configure the logger with environment variable
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, log_level, logging.INFO))

# Initialize the Kafka consumer
consumer = Consumer(
    {
        "bootstrap.servers": os.environ.get(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        ),
        "group.id": "stock-check-group",
        "auto.offset.reset": "earliest",
    }
)

consumer.subscribe(["stocks"])

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000") + "/stocks"


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
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                # Simulate random error for observability testing
                # The error rate is controlled by the ERROR_RATE environment variable (default: 0.1)
                if random.random() < ERROR_RATE:
                    logger.error("failed to process stock (API or network failure)")
                    continue

                stock_data = json.loads(msg.value().decode("utf-8"))
                logger.info("Received stock data: %s", stock_data)

                response = requests.post(API_URL, json=stock_data)
                if response.status_code == 201:
                    logger.info("Stock data successfully sent to API")
                else:
                    logger.error("Failed to send stock data to API: %s", response.text)
    except KeyboardInterrupt:
        logger.info("Consumer shutting down due to keyboard interrupt")
    finally:
        consumer.close()
        logger.info("Consumer closed")


if __name__ == "__main__":
    logger.info("SupplierCheck service starting")
    consume_messages()
