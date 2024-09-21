from pydantic import BaseModel, Field

from common.common.models import WoodType


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
