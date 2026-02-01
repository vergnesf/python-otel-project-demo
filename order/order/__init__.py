import os
import logging

from flasgger import Swagger
from flask import Flask, jsonify

from .database import DATABASE_URL, db


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Configure logging level from environment variable
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    app.logger.setLevel(getattr(logging, log_level, logging.INFO))

    db.init_app(app)

    swagger = Swagger(app)  # noqa: F841

    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "service": "order"}), 200

    with app.app_context():
        from .models import Order  # noqa: F401

        db.create_all()
        from .routes.orders import orders_bp

        app.register_blueprint(orders_bp, url_prefix="/orders")

    return app
