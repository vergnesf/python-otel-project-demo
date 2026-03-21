"""
This module contains the schemas for the brewery service.
"""

from lib_models.models import BrewStyle, IngredientType
from pydantic import BaseModel


class BrewBase(BaseModel):
    """
    Represents the base schema for a brew order.

    Attributes:
        ingredient_type (IngredientType): The type of ingredient used.
        quantity (int): The quantity of ingredient.
        brew_style (BrewStyle): The style of beer to brew.
    """

    ingredient_type: IngredientType
    quantity: int
    brew_style: BrewStyle


class BrewCreate(BrewBase):
    """
    Create a brew order based on the given brew base.
    """


class Brew(BrewBase):
    """
    The Brew class represents a brew order.

    Attributes:
        id (int): The unique identifier for the brew.
    """

    id: int
