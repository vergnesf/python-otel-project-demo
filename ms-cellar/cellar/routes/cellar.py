import logging
import os
import random

from flask import Blueprint, current_app, jsonify, request
from lib_models.models import IngredientNotFoundError, IngredientType, InsufficientIngredientError
from pydantic import ValidationError

from .. import schemas
from ..crud import (
    create_ingredient,
    decrease_ingredient_quantity,
    get_ingredient_by_type,
    get_ingredients,
)
from ..database import SessionLocal
from ..schemas import IngredientDecrease

# Configure Flask/Werkzeug logging to show HTTP errors as ERROR level
logging.getLogger("werkzeug").setLevel(logging.ERROR)

cellar_bp = Blueprint("cellar", __name__)

# Get error rate from environment variable (default 0.1)
ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))


# Custom error handler to log all HTTP error codes properly
@cellar_bp.after_request
def log_response(response):
    if response.status_code >= 500:
        current_app.logger.error(f"HTTP {response.status_code} error for {request.method} {request.path}")
    elif response.status_code >= 400:
        current_app.logger.warning(f"HTTP {response.status_code} client error for {request.method} {request.path}")
    elif 200 <= response.status_code < 300:
        current_app.logger.info(f"HTTP {response.status_code} success for {request.method} {request.path}")
    return response


@cellar_bp.route("/", methods=["POST"])
def create_ingredient_route():
    """
    Create or accumulate ingredient stock
    ---
    tags:
      - ingredients
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - ingredient_type
            - quantity
          properties:
            ingredient_type:
              type: string
            quantity:
              type: integer
    responses:
      201:
        description: Ingredient stock created or updated
        schema:
          type: object
          properties:
            ingredient_type:
              type: string
            quantity:
              type: integer
    """
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Simulated DB error during ingredient creation"}), 500
    data = request.json
    if not data:
        return jsonify({"error": "Missing request body"}), 400
    db = SessionLocal()
    try:
        ingredient_data = schemas.IngredientCreate(**data)
        new_ingredient = create_ingredient(db=db, ingredient=ingredient_data)
        return jsonify(new_ingredient.to_dict()), 201
    except Exception:
        return jsonify({"error": "Unexpected error during ingredient creation"}), 500
    finally:
        db.close()


@cellar_bp.route("/", methods=["GET"])
def read_ingredients_route():
    """
    Get a list of ingredient stocks
    ---
    tags:
      - ingredients
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
        description: List of ingredient stocks
        schema:
          type: array
          items:
            type: object
            properties:
              ingredient_type:
                type: string
              quantity:
                type: integer
    """
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Simulated API error during ingredient list"}), 502
    try:
        skip = int(request.args.get("skip", 0))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"error": "skip and limit must be integers"}), 400
    db = SessionLocal()
    try:
        ingredients = get_ingredients(db, skip=skip, limit=limit)
        return jsonify([i.to_dict() for i in ingredients]), 200
    except Exception:
        return jsonify({"error": "Unexpected error during ingredient list"}), 500
    finally:
        db.close()


@cellar_bp.route("/<ingredient_type>", methods=["GET"])
def read_ingredient_route(ingredient_type):
    """
    Get ingredient stock by type
    ---
    tags:
      - ingredients
    parameters:
      - in: path
        name: ingredient_type
        type: string
        required: true
    responses:
      200:
        description: Ingredient stock details
        schema:
          type: object
          properties:
            ingredient_type:
              type: string
            quantity:
              type: integer
      404:
        description: Ingredient not found
        schema:
          type: object
          properties:
            error:
              type: string
    """
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Simulated API error during ingredient read"}), 502
    db = SessionLocal()
    try:
        try:
            typed = IngredientType(ingredient_type)
        except ValueError:
            return jsonify({"error": f"Invalid ingredient type: {ingredient_type}"}), 400
        db_ingredient = get_ingredient_by_type(db, ingredient_type=typed)
        if db_ingredient is None:
            return jsonify({"error": "Ingredient not found"}), 404
        return jsonify(db_ingredient.to_dict()), 200
    except Exception:
        return jsonify({"error": "Unexpected error during ingredient read"}), 500
    finally:
        db.close()


@cellar_bp.route("/decrease", methods=["POST"])
def decrease_ingredient_route():
    """
    Decrease ingredient stock quantity
    ---
    tags:
      - ingredients
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - ingredient_type
            - quantity
          properties:
            ingredient_type:
              type: string
            quantity:
              type: integer
    responses:
      200:
        description: Ingredient stock quantity decreased
        schema:
          type: object
          properties:
            ingredient_type:
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
        description: Ingredient not found
        schema:
          type: object
          properties:
            error:
              type: string
    """
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Simulated DB error during ingredient decrease"}), 500
    data = request.json
    if not data:
        return jsonify({"error": "Missing request body"}), 400
    try:
        ingredient_data = IngredientDecrease(**data)
    except ValidationError:
        return jsonify({"error": "Invalid input"}), 400

    db = SessionLocal()
    try:
        decrease_ingredient_quantity(db, ingredient_type=ingredient_data.ingredient_type, quantity=ingredient_data.quantity)
        db.commit()
        db_ingredient = get_ingredient_by_type(db, ingredient_type=ingredient_data.ingredient_type)  # type: ignore[arg-type]
        if db_ingredient is None:
            return jsonify({"error": "Internal error: ingredient not found after update"}), 500
        return jsonify(db_ingredient.to_dict()), 200
    except IngredientNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except InsufficientIngredientError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "Unexpected error during ingredient decrease"}), 500
    finally:
        db.close()
