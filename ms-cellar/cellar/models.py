# pyright: reportMissingImports=false
from lib_models.models import IngredientType
from sqlalchemy import Column, Enum, Integer

from .database import db


class IngredientStockModel(db.Model):
    __tablename__ = "ingredient_stocks"

    ingredient_type = Column(Enum(IngredientType), nullable=False, primary_key=True, index=True, unique=True)
    quantity = Column(Integer, nullable=False)

    def to_dict(self):
        return {
            "ingredient_type": self.ingredient_type,
            "quantity": self.quantity,
        }
