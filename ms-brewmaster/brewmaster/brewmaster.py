import logging
import os
import random
import time

import requests
from lib_models.log_formatter import OtelJsonFormatter
from lib_models.models import BrewStatus, IngredientNotFoundError, InsufficientIngredientError
from opentelemetry import metrics, trace
from opentelemetry.trace import StatusCode

# Configure logging with environment variable
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
_handler = logging.StreamHandler()
_handler.setFormatter(OtelJsonFormatter())
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), handlers=[_handler])
logger = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)
brews_managed = meter.create_counter("brews.managed", description="Number of brews transitioned by the brewmaster")

API_URL_BREWS = os.environ.get("API_URL_BREWS", "http://127.0.0.1:8000")
API_URL_CELLAR = os.environ.get("API_URL_CELLAR", "http://127.0.0.1:8000")

API_URL_BREWS_REGISTERED = API_URL_BREWS + "/brews/status/registered"
API_URL_BREWS_UPDATE = API_URL_BREWS + "/brews"
API_URL_CELLAR_CONSUME = API_URL_CELLAR + "/ingredients/decrease"
HEADERS_JSON = {"Content-Type": "application/json"}


def fetch_registered_brews():
    try:
        response = requests.get(API_URL_BREWS_REGISTERED, timeout=5)
        response.raise_for_status()
        brews = response.json()
        return brews
    except requests.RequestException as e:
        logger.error("Failed to fetch brews: %s", e)
        return []


def consume_ingredients(brew):
    payload = {"ingredient_type": brew["ingredient_type"], "quantity": brew["quantity"]}
    response = requests.post(API_URL_CELLAR_CONSUME, headers=HEADERS_JSON, json=payload, timeout=5)
    if response.status_code == 400:
        # available=0 is a placeholder — the actual available quantity is not returned in the HTTP 400 response
        raise InsufficientIngredientError(brew["ingredient_type"], brew["quantity"], 0)
    if response.status_code == 404:
        raise IngredientNotFoundError(brew["ingredient_type"])
    response.raise_for_status()
    return response.json()


def update_brew_status(brew_id, status):
    payload = {"brew_status": status.value if hasattr(status, "value") else status}
    try:
        response = requests.put(f"{API_URL_BREWS_UPDATE}/{brew_id}", headers=HEADERS_JSON, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        resp_text = None
        if hasattr(e, "response") and e.response is not None:
            try:
                resp_text = e.response.text
            except Exception:
                resp_text = "<unable to read response body>"
        logger.error(
            "Failed to update brew %s status to %s: %s; response=%s",
            brew_id,
            payload,
            e,
            resp_text,
        )
        raise


def process_registered_brew():
    brews = fetch_registered_brews()
    ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))

    if not brews:
        return

    logger.info("Found %d registered brews to process", len(brews))

    for brew in brews:
        with tracer.start_as_current_span("process brew") as span:
            if brew.get("brew_style"):
                span.set_attribute("brew.style", brew["brew_style"])
            try:
                if random.random() < ERROR_RATE:
                    raise RuntimeError("external API or DB failure during brew processing")

                logger.info("Processing brew: %s", brew)
                consume_ingredients(brew)
                logger.info("Ingredients consumed for brew: %s", brew)
                update_brew_status(brew["id"], BrewStatus.READY)
                logger.info("Brew status updated to READY for brew: %s", brew)
                brews_managed.add(1, {"result": "ready"})
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                span.set_attribute("error.type", type(e).__name__)
                logger.error("Failed to process brew %s: %s", brew["id"], e)
                # result=blocked → real business failure (stock or ingredient not found)
                # result=error   → unexpected failure (ERROR_RATE simulation, network, etc.)
                # Increment before update_brew_status so the metric is always recorded
                # even if the status update itself fails (network error, timeout).
                result = "blocked" if isinstance(e, (InsufficientIngredientError, IngredientNotFoundError)) else "error"
                brews_managed.add(1, {"result": result})
                try:
                    update_brew_status(brew["id"], BrewStatus.BLOCKED)
                    logger.info("Brew status updated to BLOCKED for brew: %s", brew)
                except requests.RequestException as re:
                    logger.error(
                        "Could not mark brew %s as BLOCKED: %s. Continuing.",
                        brew["id"],
                        re,
                    )
                except Exception as re:
                    logger.error(
                        "Unexpected error while marking brew %s as BLOCKED: %s. Continuing.",
                        brew["id"],
                        re,
                    )


if __name__ == "__main__":
    interval_seconds = int(os.getenv("INTERVAL_SECONDS", "60"))

    logger.info("Starting brewmaster service with %d seconds interval", interval_seconds)

    while True:
        process_registered_brew()
        time.sleep(interval_seconds)
