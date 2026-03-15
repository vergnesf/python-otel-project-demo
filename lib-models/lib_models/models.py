from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class WoodType(str, Enum):
    OAK = "oak"
    MAPLE = "maple"
    BIRCH = "birch"
    ELM = "elm"
    PINE = "pine"


class OrderStatus(str, Enum):
    READY = "ready"
    SHIPPED = "shipped"
    BLOCKED = "blocked"
    CLOSED = "closed"
    UNKNOWN = "unknown"
    REGISTERED = "registered"


class Stock(BaseModel):
    wood_type: WoodType
    quantity: int


class Order(BaseModel):
    wood_type: WoodType
    quantity: int


class OrderTracking(BaseModel):
    id: int
    order_status: OrderStatus
    wood_type: WoodType
    quantity: int
    date: datetime
