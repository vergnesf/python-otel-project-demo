# pyright: reportMissingImports=false
from common_models.models import WoodType
from sqlalchemy import Column, Enum, Integer

from .database import db


class Stock(db.Model):
    __tablename__ = "stocks"

    wood_type = Column(
        Enum(WoodType), nullable=False, primary_key=True, index=True, unique=True
    )
    quantity = Column(Integer, nullable=False)

    def to_dict(self):
        return {
            "wood_type": self.wood_type,
            "quantity": self.quantity,
        }
