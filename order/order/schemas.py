"""
This module contains the schemas for the order service.
"""

from pydantic import BaseModel

from common.common.models import WoodType


class OrderBase(BaseModel):
    """
    Represents the base schema for an order.

    Attributes:
        type (WoodType): The type of wood for the order.
        quantity (int): The quantity of wood for the order.
    """

    wood_type: WoodType
    quantity: int


class OrderCreate(OrderBase):
    """
    Create an order based on the given order base.

    Parameters:
    - None

    Returns:
    - None
    """


class Order(OrderBase):
    """
    The Order class represents an order.

    Attributes:
        id (int): The unique identifier for the order.
    """

    id: int  # The unique identifier for the order

    class Config:
        """
        Configuration class for the `schemas` module.

        Attributes:
            from_attributes (bool): Config option to load attributes from the model's attributes.
        """

        from_attributes = (
            True  # Config option to load attributes from the model's attributes
        )
