import random
import os
import time
import json
import logging
import requests
from common.common.models import OrderStatus

# Configure logging with environment variable
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, log_level, logging.INFO))

API_URL_ORDERS = os.environ.get("API_URL_ORDERS", "http://127.0.0.1:8000")
API_URL_STOCKS = os.environ.get("API_URL_STOCKS", "http://127.0.0.1:8000")

API_URL_ORDERS_REGISTERED = API_URL_ORDERS + "/orders/status/registered"
API_URL_ORDERS_UPDATE = API_URL_ORDERS + "/orders"
API_URL_STOCKS_DECREASE = API_URL_STOCKS + "/stocks/decrease"
HEADERS_JSON = {"Content-Type": "application/json"}


def fetch_registered_orders():
    try:
        response = requests.get(API_URL_ORDERS_REGISTERED)
        response.raise_for_status()
        orders = response.json()
        return orders
    except requests.RequestException as e:
        logger.error(f"Failed to fetch orders: {e}")
        return []


def decrease_stock(order):
    payload = {"wood_type": order["wood_type"], "quantity": order["quantity"]}
    response = requests.post(
        API_URL_STOCKS_DECREASE, headers=HEADERS_JSON, json=payload
    )
    if response.status_code == 400:
        raise Exception("Insufficient stock")
    if response.status_code == 404:
        raise Exception("Stock not found")
    response.raise_for_status()
    return response.json()


def update_order_status(order_id, status):
    payload = {"order_status": status}
    response = requests.put(
        f"{API_URL_ORDERS_UPDATE}/{order_id}", headers=HEADERS_JSON, json=payload
    )
    response.raise_for_status()
    return response.json()


def process_registered_order():
    orders = fetch_registered_orders()
    ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))

    if not orders:
        return

    logger.info("Found %d registered orders to process", len(orders))

    for order in orders:
        try:
            # Simulate random error for observability testing
            # The error rate is controlled by the ERROR_RATE environment variable (default: 0.1)
            if random.random() < ERROR_RATE:
                # Simulate an external API or DB failure
                raise Exception(
                    "Simulated error: external API or DB failure during order processing"
                )

            logger.info("Processing order: %s", order)
            decrease_stock(order)
            logger.info("Stock decreased for order: %s", order)
            update_order_status(order["id"], OrderStatus.READY)
            logger.info("Order status updated to READY for order: %s", order)
        except Exception as e:
            logger.error(f"Failed to process order {order['id']}: {e}")
            update_order_status(order["id"], OrderStatus.BLOCKED)
            logger.info("Order status updated to BLOCKED for order: %s", order)


if __name__ == "__main__":
    interval_seconds = int(os.getenv("INTERVAL_SECONDS", 60))

    logger.info(
        "Starting order management service with %d seconds interval", interval_seconds
    )

    while True:
        process_registered_order()
        time.sleep(interval_seconds)
