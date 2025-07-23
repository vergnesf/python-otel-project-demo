import os
import logging

from flasgger import Swagger
from flask import Flask

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

    swagger = Swagger(app)

    with app.app_context():
        from .models import Stock

        db.create_all()
        from .routes.stocks import stocks_bp

        app.register_blueprint(stocks_bp, url_prefix="/stocks")

    return app
