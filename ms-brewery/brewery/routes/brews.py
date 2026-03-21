import logging
import os
import random

from flask import Blueprint, current_app, jsonify, request

from .. import schemas
from ..crud import (
    create_brew,
    get_brew,
    get_brews,
    get_brews_by_status,
    update_brew_status,
)
from ..database import SessionLocal
from ..models import BrewStatus

# Configure Flask/Werkzeug logging to show HTTP errors as ERROR level
logging.getLogger("werkzeug").setLevel(logging.ERROR)

brews_bp = Blueprint("brews", __name__)

# Get error rate from environment variable (default 0.1)
ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))

MSG_ERROR_NOT_FOUND = "Brew not found"


# Custom error handler to log all HTTP error codes properly
@brews_bp.after_request
def log_response(response):
    if response.status_code >= 500:
        current_app.logger.error(f"HTTP {response.status_code} error for {request.method} {request.path}")
    elif response.status_code >= 400:
        current_app.logger.warning(f"HTTP {response.status_code} client error for {request.method} {request.path}")
    elif 200 <= response.status_code < 300:
        current_app.logger.info(f"HTTP {response.status_code} success for {request.method} {request.path}")
    return response


@brews_bp.route("/", methods=["POST"])
def create_brew_route():
    """
    Create a new brew order
    ---
    tags:
      - brews
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - ingredient_type
            - quantity
            - brew_style
          properties:
            ingredient_type:
              type: string
            quantity:
              type: integer
            brew_style:
              type: string
    responses:
      201:
        description: Brew created successfully
        schema:
          type: object
          properties:
            id:
              type: integer
            ingredient_type:
              type: string
            quantity:
              type: integer
            brew_style:
              type: string
            brew_status:
              type: string
    """
    # Simulate DB insertion error with probability ERROR_RATE
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Simulated DB insertion error"}), 500
    data = request.json
    if not data:
        return jsonify({"error": "Missing request body"}), 400

    db = SessionLocal()
    try:
        brew_data = schemas.BrewCreate(**data)
        new_brew = create_brew(db=db, brew=brew_data)
        return jsonify(new_brew.to_dict()), 201
    except Exception:
        current_app.logger.exception("Unexpected error during brew creation")
        return (
            jsonify({"error": "Unexpected error during brew creation"}),
            500,
        )
    finally:
        db.close()


@brews_bp.route("/", methods=["GET"])
def read_brews_route():
    """
    Retrieve a list of brews
    ---
    tags:
      - brews
    parameters:
      - name: skip
        in: query
        type: integer
        required: false
        default: 0
      - name: limit
        in: query
        type: integer
        required: false
        default: 10
    responses:
      200:
        description: A list of brews
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              ingredient_type:
                type: string
              quantity:
                type: integer
              brew_style:
                type: string
              brew_status:
                type: string
    """
    # Simulate API error with probability ERROR_RATE
    if random.random() < ERROR_RATE:
        return (
            jsonify({"error": "Simulated API error during brew list"}),
            502,
        )
    try:
        skip = int(request.args.get("skip", 0))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"error": "skip and limit must be integers"}), 400

    db = SessionLocal()
    try:
        brews = get_brews(db=db, skip=skip, limit=limit)
        return jsonify([brew.to_dict() for brew in brews])
    except Exception:
        current_app.logger.exception("Unexpected error during brew list")
        return (
            jsonify({"error": "Unexpected error during brew list"}),
            500,
        )
    finally:
        db.close()


@brews_bp.route("/status/<status>", methods=["GET"])
def read_brews_by_status_route(status):
    """
    Retrieve a list of brews by status
    ---
    tags:
      - brews
    parameters:
      - name: status
        in: path
        type: string
        required: true
      - name: skip
        in: query
        type: integer
        required: false
        default: 0
      - name: limit
        in: query
        type: integer
        required: false
        default: 10
    responses:
      200:
        description: A list of brews
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              ingredient_type:
                type: string
              quantity:
                type: integer
              brew_style:
                type: string
              brew_status:
                type: string
    """
    # Simulate API error with probability ERROR_RATE
    if random.random() < ERROR_RATE:
        return (
            jsonify({"error": "Simulated API error during brew list by status"}),
            502,
        )
    try:
        skip = int(request.args.get("skip", 0))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"error": "skip and limit must be integers"}), 400

    try:
        brew_status = BrewStatus(status)
    except ValueError:
        return jsonify({"error": f"Invalid status: {status}"}), 400

    db = SessionLocal()
    try:
        brews = get_brews_by_status(db=db, brew_status=brew_status, skip=skip, limit=limit)
        return jsonify([brew.to_dict() for brew in brews])
    except Exception:
        current_app.logger.exception("Unexpected error during brew list by status")
        return (
            jsonify({"error": "Unexpected error during brew list by status"}),
            500,
        )
    finally:
        db.close()


@brews_bp.route("/<int:brew_id>", methods=["GET"])
def read_brew_route(brew_id):
    """
    Retrieve a specific brew by ID
    ---
    tags:
      - brews
    parameters:
      - name: brew_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: A brew
        schema:
          type: object
          properties:
            id:
              type: integer
            ingredient_type:
              type: string
            quantity:
              type: integer
            brew_style:
              type: string
            brew_status:
              type: string
      404:
        description: Brew not found
    """
    # Simulate API error with probability ERROR_RATE
    if random.random() < ERROR_RATE:
        return (
            jsonify({"error": "Simulated API error during brew read"}),
            502,
        )

    db = SessionLocal()
    try:
        db_brew = get_brew(db=db, brew_id=brew_id)
        if db_brew is None:
            return jsonify({"error": "Brew not found"}), 404
        return jsonify(db_brew.to_dict())
    except Exception:
        current_app.logger.exception("Unexpected error during brew read")
        return (
            jsonify({"error": "Unexpected error during brew read"}),
            500,
        )
    finally:
        db.close()


@brews_bp.route("/<int:brew_id>", methods=["PUT"])
def update_brew_status_route(brew_id):
    """
    Update the status of a specific brew
    ---
    tags:
      - brews
    parameters:
      - name: brew_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          required:
            - brew_status
          properties:
            brew_status:
              type: string
    responses:
      200:
        description: Brew updated successfully
        schema:
          type: object
          properties:
            id:
              type: integer
            ingredient_type:
              type: string
            quantity:
              type: integer
            brew_style:
              type: string
            brew_status:
              type: string
      404:
        description: Brew not found
    """
    # Simulate API error with probability ERROR_RATE
    if random.random() < ERROR_RATE:
        return (
            jsonify({"error": "Simulated API error during brew status update"}),
            502,
        )
    data = request.json
    if not data or "brew_status" not in data:
        return jsonify({"error": "Missing 'brew_status' in request body"}), 400

    try:
        brew_status = BrewStatus(data["brew_status"])
    except ValueError:
        return jsonify({"error": "Invalid brew status"}), 400

    db = SessionLocal()
    try:
        brew = get_brew(db, brew_id=brew_id)
        if brew is None:
            return jsonify({"error": "Brew not found"}), 404

        updated_brew = update_brew_status(db, brew_id=brew_id, brew_status=brew_status)

        if updated_brew is None:
            return jsonify({"error": "Brew not found"}), 404

        return jsonify(updated_brew.to_dict()), 200
    except Exception:
        current_app.logger.exception("Unexpected error during brew status update")
        return (
            jsonify({"error": "Unexpected error during brew status update"}),
            500,
        )
    finally:
        db.close()
