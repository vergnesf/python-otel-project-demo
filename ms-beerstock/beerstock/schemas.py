# pyright: reportMissingImports=false
from lib_models.models import BrewStyle
from pydantic import BaseModel, Field


class BeerStockBase(BaseModel):
    brew_style: BrewStyle
    quantity: int


class BeerStockCreate(BeerStockBase):
    pass


class BeerStockResponse(BeerStockBase):
    pass


class BeerStockShip(BaseModel):
    brew_style: str
    quantity: int = Field(gt=0, description="Quantity to ship, must be greater than zero")
