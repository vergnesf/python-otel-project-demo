from pydantic import ValidationError
from flask import Blueprint, jsonify, request, current_app
import random
import os
import logging

from .. import schemas
from ..crud import (
    create_stock,
    get_stock_by_wood_type,
    get_stocks,
    decrease_stock_quantity,
)
from ..database import get_db
from ..schemas import StockDecrease

# Configure Flask/Werkzeug logging to show HTTP errors as ERROR level
logging.getLogger("werkzeug").setLevel(logging.ERROR)

stocks_bp = Blueprint("stocks", __name__)

# Get error rate from environment variable (default 0.1)
ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))

MSG_ERROR_NOT_FOUND = "Stock not found"


# Custom error handler to log all HTTP error codes properly
@stocks_bp.after_request
def log_response(response):
    if response.status_code >= 500:
        current_app.logger.error(
            f"HTTP {response.status_code} error for {request.method} {request.path}"
        )
    elif response.status_code >= 400:
        current_app.logger.warning(
            f"HTTP {response.status_code} client error for {request.method} {request.path}"
        )
    elif response.status_code == 200:
        current_app.logger.debug(
            f"HTTP {response.status_code} success for {request.method} {request.path}"
        )
    return response


@stocks_bp.route("/", methods=["POST"])
def create_stock_route():
    """
    Create a new stock
    ---
    tags:
      - stocks
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - wood_type
            - quantity
          properties:
            wood_type:
              type: string
            quantity:
              type: integer
    responses:
      201:
        description: Stock created successfully
        schema:
          type: object
          properties:
            id:
              type: integer
            wood_type:
              type: string
            quantity:
              type: integer
    """
    # Simulate DB/API error with probability ERROR_RATE
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Simulated DB error during stock creation"}), 500
    data = request.json
    db = next(get_db())
    stock_data = schemas.StockCreate(**data)
    try:
        new_stock = create_stock(db=db, stock=stock_data)
    except Exception:
        return jsonify({"error": "Unexpected error during stock creation"}), 500
    return jsonify(new_stock.to_dict()), 201


@stocks_bp.route("/", methods=["GET"])
def read_stocks_route():
    """
    Get a list of stocks
    ---
    tags:
      - stocks
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
        description: List of stocks
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              wood_type:
                type: string
              quantity:
                type: integer
    """
    # Simulate API error with probability ERROR_RATE
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Simulated API error during stock list"}), 502
    skip = int(request.args.get("skip", 0))
    limit = int(request.args.get("limit", 10))
    db = next(get_db())
    try:
        stocks = get_stocks(db, skip=skip, limit=limit)
    except Exception:
        return jsonify({"error": "Unexpected error during stock list"}), 500
    return jsonify([stock.to_dict() for stock in stocks]), 200


@stocks_bp.route("/<wood_type>", methods=["GET"])
def read_stock_route(wood_type):
    """
    Get a stock by wood type
    ---
    tags:
      - stocks
    parameters:
      - in: path
        name: wood_type
        type: string
        required: true
    responses:
      200:
        description: Stock details
        schema:
          type: object
          properties:
            id:
              type: integer
            wood_type:
              type: string
            quantity:
              type: integer
      404:
        description: Stock not found
        schema:
          type: object
          properties:
            error:
              type: string
    """
    # Simulate API error with probability ERROR_RATE
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Simulated API error during stock read"}), 502
    db = next(get_db())
    try:
        db_stock = get_stock_by_wood_type(db, wood_type=wood_type)
    except Exception:
        return jsonify({"error": "Unexpected error during stock read"}), 500
    if db_stock is None:
        return jsonify({"error": MSG_ERROR_NOT_FOUND}), 404
    return jsonify(db_stock.to_dict()), 200


@stocks_bp.route("/decrease", methods=["POST"])
def decrease_stock_route():
    """
    Decrease stock quantity
    ---
    tags:
      - stocks
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - wood_type
            - quantity
          properties:
            wood_type:
              type: string
            quantity:
              type: integer
    responses:
      200:
        description: Stock quantity decreased
        schema:
          type: object
          properties:
            id:
              type: integer
            wood_type:
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
      404:
        description: Stock not found
        schema:
          type: object
          properties:
            error:
              type: string
    """
    # Simulate DB/API error with probability ERROR_RATE
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Simulated DB error during stock decrease"}), 500
    data = request.json
    try:
        stock_data = StockDecrease(**data)
    except ValidationError:
        return jsonify({"error": "Invalid input"}), 400

    db = next(get_db())
    try:
        db_stock = get_stock_by_wood_type(db, wood_type=stock_data.wood_type)
    except Exception:
        return jsonify({"error": "Unexpected error during stock decrease (read)"}), 500
    if db_stock is None:
        return jsonify({"error": "Stock not found"}), 404

    if db_stock.quantity < stock_data.quantity:
        return jsonify({"error": "Insufficient stock"}), 400

    try:
        decrease_stock_quantity(
            db, wood_type=stock_data.wood_type, quantity=stock_data.quantity
        )
        db.commit()
        db.refresh(db_stock)
    except Exception:
        return (
            jsonify({"error": "Unexpected error during stock decrease (update)"}),
            500,
        )
    return jsonify(db_stock.to_dict()), 200
