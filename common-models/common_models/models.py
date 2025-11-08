# Fichier: src/common/models.py
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

    def to_json(self):
        return self.model_dump_json()


class Order(BaseModel):
    wood_type: WoodType
    quantity: int

    def to_json(self):
        return self.model_dump_json()


class OrderTracking(BaseModel):
    id: int
    order_status: OrderStatus
    wood_type: WoodType
    quantity: int
    date: datetime

    def to_json(self):
        return self.model_dump_json()
