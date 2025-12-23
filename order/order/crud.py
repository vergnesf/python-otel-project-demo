"""
This module provides CRUD operations for orders.
"""

from sqlalchemy.orm import Session

from common_models.models import OrderStatus

from . import models, schemas


def get_order(db: Session, order_id: int):
    """
    Retrieve an order by its ID.
    """
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_orders(db: Session, skip: int = 0, limit: int = 10):
    """
    Retrieve a list of orders with optional pagination.
    """
    return db.query(models.Order).offset(skip).limit(limit).all()


def get_orders_by_status(
    db: Session, order_status: OrderStatus, skip: int = 0, limit: int = 10
):
    """
    Retrieve a list of orders by status with optional pagination.
    """
    return (
        db.query(models.Order)
        .filter(models.Order.order_status == order_status)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_order_status(db: Session, order_id: int, order_status: OrderStatus):
    """
    Update the status of an order.
    """
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if db_order:
        db_order.order_status = order_status  # type: ignore[misc]
        db.commit()
        db.refresh(db_order)
    return db_order


def create_order(db: Session, order: schemas.OrderCreate):
    """
    Create a new order.
    """
    db_order = models.Order(
        wood_type=order.wood_type,
        quantity=order.quantity,
        order_status=OrderStatus.REGISTERED,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


def delete_order(db: Session, order_id: int):
    """
    Delete an order by its ID.
    """
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if db_order:
        db.delete(db_order)
        db.commit()
    return db_order
