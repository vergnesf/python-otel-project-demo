from datetime import datetime
from enum import Enum

from pydantic import BaseModel


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


class IngredientStock(BaseModel):
    ingredient_type: IngredientType
    quantity: int


class BrewOrder(BaseModel):
    ingredient_type: IngredientType
    quantity: int
    brew_style: BrewStyle


class BrewTracking(BaseModel):
    id: int
    brew_status: BrewStatus
    ingredient_type: IngredientType
    quantity: int
    brew_style: BrewStyle
    date: datetime


class InsufficientIngredientError(Exception):
    pass


class IngredientNotFoundError(Exception):
    pass
