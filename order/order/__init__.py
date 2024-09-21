import os

from flasgger import Swagger
from flask import Flask

from .database import DATABASE_URL, db


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    swagger = Swagger(app)

    with app.app_context():
        from .models import Order

        db.create_all()
        from .routes.orders import orders_bp

        app.register_blueprint(orders_bp, url_prefix="/orders")

    return app
