from flask import Blueprint, jsonify, request

from .. import schemas
from ..crud import (
    create_order,
    get_order,
    get_orders,
    get_orders_by_status,
    update_order_status,
)
from ..database import get_db
from ..models import OrderStatus

orders_bp = Blueprint("orders", __name__)

MSG_ERROR_NOT_FOUND = "Order not found"


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
    data = request.json
    db = next(get_db())
    order_data = schemas.OrderCreate(**data)
    new_order = create_order(db=db, order=order_data)
    return jsonify(new_order.to_dict()), 201


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
    skip = int(request.args.get("skip", 0))
    limit = int(request.args.get("limit", 10))
    db = next(get_db())
    orders = get_orders(db=db, skip=skip, limit=limit)
    return jsonify([order.to_dict() for order in orders])


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
    skip = int(request.args.get("skip", 0))
    limit = int(request.args.get("limit", 10))
    db = next(get_db())
    orders = get_orders_by_status(
        db=db, order_status=OrderStatus(status), skip=skip, limit=limit
    )
    return jsonify([order.to_dict() for order in orders])


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
    db = next(get_db())
    db_order = get_order(db=db, order_id=order_id)
    if db_order is None:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(db_order.to_dict())


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
    data = request.json
    if "order_status" not in data:
        return jsonify({"error": "Missing 'order_status' in request body"}), 400

    try:
        order_status = OrderStatus(data["order_status"])
    except ValueError:
        return jsonify({"error": "Invalid order status"}), 400

    db = next(get_db())
    order = get_order(db, order_id=order_id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404

    updated_order = update_order_status(
        db, order_id=order_id, order_status=order_status
    )
    return jsonify(updated_order.to_dict()), 200
