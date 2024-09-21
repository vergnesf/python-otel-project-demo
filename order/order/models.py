"""
This module contains the SQLAlchemy model for the Order entity.
"""

from sqlalchemy import Column, Enum, Integer

from common.common.models import OrderStatus, WoodType

from .database import db


class Order(db.Model):
    """
    Represents an order.

    Attributes:
        id (int): The unique identifier of the order.
        type (WoodType): The type of wood for the order.
        quantity (int): The quantity of wood for the order.
        status (OrderStatus): The status of the order.
    """

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    wood_type = Column(Enum(WoodType), nullable=False)
    quantity = Column(Integer, nullable=False)
    order_status = Column(Enum(OrderStatus), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "wood_type": self.wood_type,
            "quantity": self.quantity,
            "order_status": self.order_status,
        }
