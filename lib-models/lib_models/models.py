from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class IngredientType(str, Enum):
    MALT = "malt"
    HOPS = "hops"
    YEAST = "yeast"
    WHEAT = "wheat"
    BARLEY = "barley"


class BrewStatus(str, Enum):
    REGISTERED = "registered"
    BREWING = "brewing"
    READY = "ready"
    SHIPPED = "shipped"
    BLOCKED = "blocked"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class BrewStyle(str, Enum):
    LAGER = "lager"
    IPA = "ipa"
    STOUT = "stout"
    WHEAT_BEER = "wheat_beer"


PositiveInt = Annotated[int, Field(gt=0)]


class IngredientStock(BaseModel):
    ingredient_type: IngredientType
    quantity: PositiveInt


class BrewOrder(BaseModel):
    ingredient_type: IngredientType
    quantity: PositiveInt
    brew_style: BrewStyle


class BrewTracking(BaseModel):
    id: int
    brew_status: BrewStatus
    ingredient_type: IngredientType
    quantity: PositiveInt
    brew_style: BrewStyle
    date: datetime


class BeerStock(BaseModel):
    brew_style: BrewStyle
    quantity: int


class InsufficientIngredientError(Exception):
    def __init__(self, ingredient_type: str, requested: int, available: int) -> None:
        self.ingredient_type = ingredient_type
        self.requested = requested
        self.available = available
        super().__init__(f"Insufficient {ingredient_type}: requested {requested}, available {available}")


class IngredientNotFoundError(Exception):
    def __init__(self, ingredient_type: str) -> None:
        self.ingredient_type = ingredient_type
        super().__init__(f"Ingredient not found: {ingredient_type}")


class InsufficientBeerStockError(Exception):
    def __init__(self, brew_style: str, requested: int, available: int) -> None:
        self.brew_style = brew_style
        self.requested = requested
        self.available = available
        super().__init__(f"Insufficient beer stock for {brew_style}: requested {requested}, available {available}")
