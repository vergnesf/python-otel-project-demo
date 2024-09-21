from pydantic import ValidationError
from flask import Blueprint, jsonify, request

from .. import schemas
from ..crud import (
    create_stock,
    get_stock_by_wood_type,
    get_stocks,
    decrease_stock_quantity,
)
from ..database import get_db
from ..schemas import StockDecrease

stocks_bp = Blueprint("stocks", __name__)

MSG_ERROR_NOT_FOUND = "Stock not found"


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
    data = request.json
    db = next(get_db())
    stock_data = schemas.StockCreate(**data)
    new_stock = create_stock(db=db, stock=stock_data)
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
    skip = int(request.args.get("skip", 0))
    limit = int(request.args.get("limit", 10))
    db = next(get_db())
    stocks = get_stocks(db, skip=skip, limit=limit)
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
    db = next(get_db())
    db_stock = get_stock_by_wood_type(db, wood_type=wood_type)
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
    data = request.json
    try:
        stock_data = StockDecrease(**data)
    except ValidationError as e:
        return jsonify({"error": "Invalid input"}), 400

    db = next(get_db())
    db_stock = get_stock_by_wood_type(db, wood_type=stock_data.wood_type)
    if db_stock is None:
        return jsonify({"error": "Stock not found"}), 404

    if db_stock.quantity < stock_data.quantity:
        return jsonify({"error": "Insufficient stock"}), 400

    decrease_stock_quantity(
        db, wood_type=stock_data.wood_type, quantity=stock_data.quantity
    )
    db.commit()
    db.refresh(db_stock)
    return jsonify(db_stock.to_dict()), 200
