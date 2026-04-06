import logging
import os
import random

from flask import Blueprint, current_app, jsonify, request
from lib_models.models import BrewStyle, InsufficientBeerStockError
from pydantic import ValidationError

from .. import schemas
from ..crud import (
    create_beer_stock,
    get_beer_stock_by_style,
    get_beer_stocks,
    ship_beer_stock,
)
from ..database import SessionLocal
from ..schemas import BeerStockShip

# Configure Flask/Werkzeug logging to show HTTP errors as ERROR level
logging.getLogger("werkzeug").setLevel(logging.ERROR)

beerstock_bp = Blueprint("beerstock", __name__)

# Get error rate from environment variable (default 0.1)
ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))


# Custom error handler to log all HTTP error codes properly
@beerstock_bp.after_request
def log_response(response):
    if response.status_code >= 500:
        current_app.logger.error(f"HTTP {response.status_code} error for {request.method} {request.path}")
    elif response.status_code >= 400:
        current_app.logger.warning(f"HTTP {response.status_code} client error for {request.method} {request.path}")
    elif 200 <= response.status_code < 300:
        current_app.logger.info(f"HTTP {response.status_code} success for {request.method} {request.path}")
    return response


@beerstock_bp.route("/", methods=["POST"])
def create_beer_stock_route():
    """
    Add finished beer to stock
    ---
    tags:
      - beerstock
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - brew_style
            - quantity
          properties:
            brew_style:
              type: string
            quantity:
              type: integer
    responses:
      201:
        description: Beer stock created or updated
        schema:
          type: object
          properties:
            brew_style:
              type: string
            quantity:
              type: integer
    """
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Simulated DB error during beer stock creation"}), 500
    data = request.json
    if not data:
        return jsonify({"error": "Missing request body"}), 400
    db = SessionLocal()
    try:
        stock_data = schemas.BeerStockCreate(**data)
        new_stock = create_beer_stock(db=db, stock=stock_data)
        return jsonify(new_stock.to_dict()), 201
    except Exception:
        return jsonify({"error": "Unexpected error during beer stock creation"}), 500
    finally:
        db.close()


@beerstock_bp.route("/", methods=["GET"])
def read_beer_stocks_route():
    """
    Get a list of beer stocks
    ---
    tags:
      - beerstock
    parameters:
      - in: query
        name: skip
        type: integer
        required: false
        default: 0
      - in: query
        name: limit
        type: integer
        required: false
        default: 10
    responses:
      200:
        description: List of beer stocks
        schema:
          type: array
          items:
            type: object
            properties:
              brew_style:
                type: string
              quantity:
                type: integer
    """
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Simulated API error during beer stock list"}), 502
    try:
        skip = int(request.args.get("skip", 0))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"error": "skip and limit must be integers"}), 400
    db = SessionLocal()
    try:
        stocks = get_beer_stocks(db, skip=skip, limit=limit)
        return jsonify([s.to_dict() for s in stocks]), 200
    except Exception:
        return jsonify({"error": "Unexpected error during beer stock list"}), 500
    finally:
        db.close()


@beerstock_bp.route("/<brew_style>", methods=["GET"])
def read_beer_stock_route(brew_style):
    """
    Get beer stock by style
    ---
    tags:
      - beerstock
    parameters:
      - in: path
        name: brew_style
        type: string
        required: true
    responses:
      200:
        description: Beer stock details
        schema:
          type: object
          properties:
            brew_style:
              type: string
            quantity:
              type: integer
      404:
        description: Beer stock not found
        schema:
          type: object
          properties:
            error:
              type: string
    """
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Simulated API error during beer stock read"}), 502
    db = SessionLocal()
    try:
        try:
            typed = BrewStyle(brew_style)
        except ValueError:
            return jsonify({"error": f"Invalid brew style: {brew_style}"}), 400
        db_stock = get_beer_stock_by_style(db, brew_style=typed)
        if db_stock is None:
            return jsonify({"error": "Beer stock not found"}), 404
        return jsonify(db_stock.to_dict()), 200
    except Exception:
        return jsonify({"error": "Unexpected error during beer stock read"}), 500
    finally:
        db.close()


@beerstock_bp.route("/ship", methods=["POST"])
def ship_beer_stock_route():
    """
    Decrease beer stock quantity (ship an order)
    ---
    tags:
      - beerstock
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - brew_style
            - quantity
          properties:
            brew_style:
              type: string
            quantity:
              type: integer
    responses:
      200:
        description: Beer stock quantity decreased
        schema:
          type: object
          properties:
            brew_style:
              type: string
            quantity:
              type: integer
      400:
        description: Insufficient stock
        schema:
          type: object
          properties:
            error:
              type: string
    """
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Simulated DB error during beer stock ship"}), 500
    data = request.json
    if not data:
        return jsonify({"error": "Missing request body"}), 400
    try:
        ship_data = BeerStockShip(**data)
    except ValidationError:
        return jsonify({"error": "Invalid input"}), 400

    db = SessionLocal()
    try:
        ship_beer_stock(db, brew_style=ship_data.brew_style, quantity=ship_data.quantity)
        db.commit()
        db_stock = get_beer_stock_by_style(db, brew_style=ship_data.brew_style)  # type: ignore[arg-type]
        if db_stock is None:
            return jsonify({"error": "Internal error: stock not found after update"}), 500
        return jsonify(db_stock.to_dict()), 200
    except InsufficientBeerStockError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "Unexpected error during beer stock ship"}), 500
    finally:
        db.close()
