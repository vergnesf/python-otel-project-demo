"""
This module contains the SQLAlchemy model for the Brew entity.
"""

from lib_models.models import BrewStatus, BrewStyle, IngredientType
from sqlalchemy import Column, Enum, Integer

from .database import db


class BrewModel(db.Model):
    """
    Represents a brew order.

    Attributes:
        id (int): The unique identifier of the brew.
        ingredient_type (IngredientType): The type of ingredient used.
        quantity (int): The quantity of ingredient.
        brew_style (BrewStyle): The style of beer to brew.
        brew_status (BrewStatus): The current status of the brew.
    """

    __tablename__ = "brews"

    id = Column(Integer, primary_key=True, index=True)
    ingredient_type = Column(Enum(IngredientType), nullable=False)
    quantity = Column(Integer, nullable=False)
    brew_style = Column(Enum(BrewStyle), nullable=False)
    brew_status = Column(Enum(BrewStatus), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "ingredient_type": (self.ingredient_type.value if hasattr(self.ingredient_type, "value") else self.ingredient_type),
            "quantity": self.quantity,
            "brew_style": (self.brew_style.value if hasattr(self.brew_style, "value") else self.brew_style),
            "brew_status": (self.brew_status.value if hasattr(self.brew_status, "value") else self.brew_status),
        }
