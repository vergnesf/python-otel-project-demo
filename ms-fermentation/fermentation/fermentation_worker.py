import logging
import os
import random
import signal
import time

import requests
from lib_models.log_formatter import OtelJsonFormatter
from lib_models.models import BrewStatus
from opentelemetry import trace
from opentelemetry.trace import StatusCode

# Configure logging with environment variable
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
_handler = logging.StreamHandler()
_handler.setFormatter(OtelJsonFormatter())
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), handlers=[_handler])
logger = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__)

API_URL_BREWS = os.environ.get("API_URL_BREWS", "http://brewery:5000")
API_URL_BREWS_BREWING = API_URL_BREWS + "/brews/status/brewing"
API_URL_BREWS_UPDATE = API_URL_BREWS + "/brews"
HEADERS_JSON = {"Content-Type": "application/json"}

# In-memory tracking of fermentation start times per brew_id.
# Keyed by brew_id (int), value is monotonic clock time at first observation.
_fermentation_start: dict[int, float] = {}


def fetch_brewing_brews() -> list:
    try:
        response = requests.get(API_URL_BREWS_BREWING, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        with tracer.start_as_current_span("fetch brewing brews") as span:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            span.set_attribute("error.type", type(e).__name__)
        logger.error("Failed to fetch brewing brews: %s", e)
        return []


def update_brew_status(brew_id: int, status: BrewStatus) -> None:
    payload = {"brew_status": status.value}
    response = requests.put(f"{API_URL_BREWS_UPDATE}/{brew_id}", headers=HEADERS_JSON, json=payload, timeout=5)
    response.raise_for_status()


def process_brewing_brews(fermentation_seconds: float, error_rate: float) -> None:
    brews = fetch_brewing_brews()

    # Clean up tracking for brews that are no longer in BREWING status
    # (e.g., moved to BLOCKED by ms-brewmaster before fermentation completes)
    current_brewing_ids = {brew["id"] for brew in brews}
    stale_ids = [bid for bid in list(_fermentation_start) if bid not in current_brewing_ids]
    for bid in stale_ids:
        logger.info("Brew %d no longer in BREWING status, removing from fermentation tracking", bid)
        del _fermentation_start[bid]

    if not brews:
        return

    now = time.monotonic()
    logger.info("Found %d brewing brew(s) to check", len(brews))

    for brew in brews:
        brew_id = brew["id"]

        just_started = brew_id not in _fermentation_start
        if just_started:
            _fermentation_start[brew_id] = now

        elapsed = now - _fermentation_start[brew_id]
        progress_pct = min(elapsed / fermentation_seconds * 100.0, 100.0)
        fermentation_complete = elapsed >= fermentation_seconds

        # Span name follows the issue spec: "ferment brew" with SpanKind.INTERNAL (default)
        with tracer.start_as_current_span("ferment brew") as span:
            span.set_attribute("brew.style", brew.get("brew_style", "unknown"))
            span.set_attribute("brew.ingredient_type", brew.get("ingredient_type", "unknown"))
            span.set_attribute("fermentation.progress_pct", round(progress_pct, 1))

            if just_started:
                span.add_event("fermentation.started")

            if fermentation_complete:
                span.add_event("fermentation.complete")
                try:
                    if random.random() < error_rate:
                        raise RuntimeError("simulated failure during fermentation completion")
                    update_brew_status(brew_id, BrewStatus.READY)
                    logger.info("Brew %d fermentation complete → READY", brew_id)
                    del _fermentation_start[brew_id]
                except Exception as e:
                    span.set_status(StatusCode.ERROR, str(e))
                    span.record_exception(e)
                    span.set_attribute("error.type", type(e).__name__)
                    logger.error("Failed to complete fermentation for brew %d: %s", brew_id, e)
            else:
                logger.info("Brew %d fermenting: %.1f%% (%.0fs / %.0fs)", brew_id, progress_pct, elapsed, fermentation_seconds)


if __name__ == "__main__":
    try:
        fermentation_seconds = float(os.getenv("FERMENTATION_SECONDS", "30"))
    except ValueError:
        logger.error("Invalid FERMENTATION_SECONDS value, must be a float. Using default 30.")
        fermentation_seconds = 30.0
    if fermentation_seconds <= 0:
        logger.warning("FERMENTATION_SECONDS=%.0f must be > 0 — clamping to 1", fermentation_seconds)
        fermentation_seconds = 1.0
    try:
        interval_seconds = int(os.getenv("INTERVAL_SECONDS", "10"))
    except ValueError:
        logger.error("Invalid INTERVAL_SECONDS value, must be an integer. Using default 10.")
        interval_seconds = 10
    if interval_seconds < 1:
        logger.warning("INTERVAL_SECONDS=%d is less than 1 — clamping to 1 to avoid busy-loop", interval_seconds)
        interval_seconds = 1
    try:
        error_rate = float(os.environ.get("ERROR_RATE", 0.1))
    except ValueError:
        logger.error("Invalid ERROR_RATE value, must be a float. Using default 0.1.")
        error_rate = 0.1
    if not 0.0 <= error_rate <= 1.0:
        logger.warning("ERROR_RATE=%.2f is outside [0.0, 1.0] — clamping", error_rate)
        error_rate = max(0.0, min(1.0, error_rate))

    logger.info(
        "Fermentation service starting: FERMENTATION_SECONDS=%.0f, INTERVAL_SECONDS=%d, ERROR_RATE=%.2f",
        fermentation_seconds,
        interval_seconds,
        error_rate,
    )

    running = True

    def _shutdown(signum, frame):
        global running
        logger.info("Received signal %s, shutting down", signum)
        running = False

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    while running:
        process_brewing_brews(fermentation_seconds, error_rate)
        time.sleep(interval_seconds)

    logger.info("Fermentation worker stopped")
