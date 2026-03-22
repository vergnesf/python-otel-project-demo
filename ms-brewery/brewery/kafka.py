import json
import logging
import os

from opentelemetry.propagate import inject

logger = logging.getLogger(__name__)

_kafka_bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
_producer = None

if _kafka_bootstrap:
    from confluent_kafka import Producer

    _producer = Producer({"bootstrap.servers": _kafka_bootstrap})


def _delivery_report(err, msg):
    if err is not None:
        logger.error("brews-ready delivery failed: %s", err)
    else:
        logger.info("brews-ready delivered to %s [%d]", msg.topic(), msg.partition())


def publish_brew_ready(brew_dict: dict) -> None:
    """Publish a brew dict to the brews-ready Kafka topic.

    Injects the current W3C trace context into message headers so that
    ms-quality-control can link its consumer span to this producer context.
    Silently skips if KAFKA_BOOTSTRAP_SERVERS is not configured (e.g. unit tests).
    """
    if _producer is None:
        return
    headers: dict[str, str] = {}
    inject(headers)
    _producer.produce(
        "brews-ready",
        value=json.dumps(brew_dict),
        headers=list(headers.items()),
        callback=_delivery_report,
    )
    _producer.poll(0)
