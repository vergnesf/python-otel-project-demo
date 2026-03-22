import logging
import os
import time

from flasgger import Swagger
from flask import Flask, g, jsonify, request
from lib_models.log_formatter import OtelJsonFormatter
from opentelemetry import metrics

from .database import DATABASE_URL, db

_meter = metrics.get_meter("ms-beerstock")
_http_duration = _meter.create_histogram("beerstock.http.duration", unit="s", description="HTTP request duration per endpoint")


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Configure logging level from environment variable
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    _handler = logging.StreamHandler()
    _handler.setFormatter(OtelJsonFormatter())
    logging.basicConfig(level=getattr(logging, log_level, logging.INFO), handlers=[_handler])
    app.logger.setLevel(getattr(logging, log_level, logging.INFO))

    db.init_app(app)

    swagger = Swagger(app)  # noqa: F841

    @app.before_request
    def _start_timer():
        g.start_time = time.monotonic()

    @app.after_request
    def _record_duration(response):
        duration = time.monotonic() - g.get("start_time", time.monotonic())
        # Use url_rule (e.g. "/ship") instead of path to avoid high cardinality.
        route = str(request.url_rule) if request.url_rule else request.path
        _http_duration.record(duration, {"http.method": request.method, "http.route": route, "http.status_code": str(response.status_code)})
        return response

    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "service": "beerstock"}), 200

    with app.app_context():
        from .models import BeerStockModel  # noqa: F401

        db.create_all()
        from .routes.beerstock import beerstock_bp

        app.register_blueprint(beerstock_bp, url_prefix="/beerstock")

    return app
