import json
import logging
import os
import sys

import requests
from confluent_kafka import Consumer, KafkaError, KafkaException

from common.common.models import Stock, WoodType

# Configure the logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the 'common' module path to PYTHONPATH
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../common"))
)

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
                stock_data = json.loads(msg.value().decode("utf-8"))
                logger.info("Received stock data: %s", stock_data)
                response = requests.post(API_URL, json=stock_data)
                if response.status_code == 201:
                    logger.info("Stock data successfully sent to API")
                else:
                    logger.error("Failed to send stock data to API: %s", response.text)
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


if __name__ == "__main__":
    consume_messages()
