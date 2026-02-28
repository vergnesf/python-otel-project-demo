# pyright: reportMissingImports=false
from common_models.models import WoodType
from pydantic import BaseModel, Field


class StockBase(BaseModel):
    wood_type: WoodType
    quantity: int


class StockCreate(StockBase):
    pass


class Stock(StockBase):
    pass


class StockDecrease(BaseModel):
    wood_type: str
    quantity: int = Field(
        gt=0, description="Quantity to decrease, must be greater than zero"
    )
