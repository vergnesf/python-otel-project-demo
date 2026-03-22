# pyright: reportMissingImports=false
from lib_models.models import BrewStyle
from sqlalchemy import Column, Enum, Integer

from .database import db


class BeerStockModel(db.Model):
    __tablename__ = "beer_stocks"

    brew_style = Column(Enum(BrewStyle), nullable=False, primary_key=True, index=True, unique=True)
    quantity = Column(Integer, nullable=False)

    def to_dict(self):
        return {
            "brew_style": self.brew_style,
            "quantity": self.quantity,
        }
