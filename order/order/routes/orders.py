from flask import Blueprint, jsonify, request, current_app
import random
import os
import logging

from .. import schemas
from ..crud import (
    create_order,
    get_order,
    get_orders,
    get_orders_by_status,
    update_order_status,
)
from ..database import SessionLocal
from ..models import OrderStatus

# Configure Flask/Werkzeug logging to show HTTP errors as ERROR level
logging.getLogger("werkzeug").setLevel(logging.ERROR)

orders_bp = Blueprint("orders", __name__)

# Get error rate from environment variable (default 0.1)
ERROR_RATE = float(os.environ.get("ERROR_RATE", 0.1))

MSG_ERROR_NOT_FOUND = "Order not found"


# Custom error handler to log all HTTP error codes properly
@orders_bp.after_request
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


@orders_bp.route("/", methods=["POST"])
def create_order_route():
    """
    Create a new order
    ---
    tags:
      - orders
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - type
            - quantity
          properties:
            type:
              type: string
            quantity:
              type: integer
    responses:
      201:
        description: Order created successfully
        schema:
          type: object
          properties:
            id:
              type: integer
            type:
              type: string
            quantity:
              type: integer
            status:
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
        order_data = schemas.OrderCreate(**data)
        new_order = create_order(db=db, order=order_data)
        return jsonify(new_order.to_dict()), 201
    except Exception as e:
        current_app.logger.exception("Unexpected error during order creation")
        return (
            jsonify({"error": "Unexpected error during order creation"}),
            500,
        )
    finally:
        db.close()


@orders_bp.route("/", methods=["GET"])
def read_orders_route():
    """
    Retrieve a list of orders
    ---
    tags:
      - orders
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
        description: A list of orders
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              type:
                type: string
              quantity:
                type: integer
              status:
                type: string
    """
    # Simulate API error with probability ERROR_RATE
    if random.random() < ERROR_RATE:
        return (
            jsonify({"error": "Simulated API error during order list"}),
            502,
        )
    skip = int(request.args.get("skip", 0))
    limit = int(request.args.get("limit", 10))

    db = SessionLocal()
    try:
        orders = get_orders(db=db, skip=skip, limit=limit)
        return jsonify([order.to_dict() for order in orders])
    except Exception as e:
        current_app.logger.exception("Unexpected error during order list")
        return (
            jsonify({"error": "Unexpected error during order list"}),
            500,
        )
    finally:
        db.close()


@orders_bp.route("/status/<status>", methods=["GET"])
def read_orders_by_status_route(status):
    """
    Retrieve a list of orders by status
    ---
    tags:
      - orders
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
        description: A list of orders
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              type:
                type: string
              quantity:
                type: integer
              status:
                type: string
    """
    # Simulate API error with probability ERROR_RATE
    if random.random() < ERROR_RATE:
        return (
            jsonify({"error": "Simulated API error during order list by status"}),
            502,
        )
    skip = int(request.args.get("skip", 0))
    limit = int(request.args.get("limit", 10))

    db = SessionLocal()
    try:
        orders = get_orders_by_status(
            db=db, order_status=OrderStatus(status), skip=skip, limit=limit
        )
        return jsonify([order.to_dict() for order in orders])
    except Exception as e:
        current_app.logger.exception("Unexpected error during order list by status")
        return (
            jsonify({"error": "Unexpected error during order list by status"}),
            500,
        )
    finally:
        db.close()


@orders_bp.route("/<int:order_id>", methods=["GET"])
def read_order_route(order_id):
    """
    Retrieve a specific order by ID
    ---
    tags:
      - orders
    parameters:
      - name: order_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: An order
        schema:
          type: object
          properties:
            id:
              type: integer
            type:
              type: string
            quantity:
              type: integer
            status:
              type: string
      404:
        description: Order not found
    """
    # Simulate API error with probability ERROR_RATE
    if random.random() < ERROR_RATE:
        return (
            jsonify({"error": "Simulated API error during order read"}),
            502,
        )

    db = SessionLocal()
    try:
        db_order = get_order(db=db, order_id=order_id)
        if db_order is None:
            return jsonify({"error": "Order not found"}), 404
        return jsonify(db_order.to_dict())
    except Exception as e:
        current_app.logger.exception("Unexpected error during order read")
        return (
            jsonify({"error": "Unexpected error during order read"}),
            500,
        )
    finally:
        db.close()


@orders_bp.route("/<int:order_id>", methods=["PUT"])
def update_order_status_route(order_id):
    """
    Update the status of a specific order
    ---
    tags:
      - orders
    parameters:
      - name: order_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
    responses:
      200:
        description: Order updated successfully
        schema:
          type: object
          properties:
            id:
              type: integer
            type:
              type: string
            quantity:
              type: integer
            status:
              type: string
      404:
        description: Order not found
    """
    # Simulate API error with probability ERROR_RATE
    if random.random() < ERROR_RATE:
        return (
            jsonify({"error": "Simulated API error during order status update"}),
            502,
        )
    data = request.json
    if not data or "order_status" not in data:
        return jsonify({"error": "Missing 'order_status' in request body"}), 400

    try:
        order_status = OrderStatus(data["order_status"])
    except ValueError:
        return jsonify({"error": "Invalid order status"}), 400

    db = SessionLocal()
    try:
        order = get_order(db, order_id=order_id)
        if order is None:
            return jsonify({"error": "Order not found"}), 404

        updated_order = update_order_status(
            db, order_id=order_id, order_status=order_status
        )

        if updated_order is None:
            return jsonify({"error": "Order not found"}), 404

        return jsonify(updated_order.to_dict()), 200
    except Exception as e:
        current_app.logger.exception("Unexpected error during order status update")
        return (
            jsonify({"error": "Unexpected error during order status update"}),
            500,
        )
    finally:
        db.close()
