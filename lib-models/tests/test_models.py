"""Unit tests for lib_models.models — shared Pydantic v2 data contracts.

Coverage:
- WoodType enum: all 5 values, invalid value rejection
- OrderStatus enum: all 6 values, invalid value rejection
- Stock: instantiation, type validation, to_json() round-trip
- Order: instantiation, type validation, to_json() round-trip
- OrderTracking: instantiation with datetime, all fields, to_json()
"""

import json
from datetime import datetime

import pytest
from lib_models.models import Order, OrderStatus, OrderTracking, Stock, WoodType
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# WoodType
# ---------------------------------------------------------------------------


def test_wood_type_all_values():
    assert set(WoodType) == {
        WoodType.OAK,
        WoodType.MAPLE,
        WoodType.BIRCH,
        WoodType.ELM,
        WoodType.PINE,
    }


def test_wood_type_string_values():
    assert WoodType.OAK == "oak"
    assert WoodType.MAPLE == "maple"
    assert WoodType.BIRCH == "birch"
    assert WoodType.ELM == "elm"
    assert WoodType.PINE == "pine"


def test_wood_type_invalid_value_raises():
    with pytest.raises(ValueError):
        WoodType("walnut")


# ---------------------------------------------------------------------------
# OrderStatus
# ---------------------------------------------------------------------------


def test_order_status_all_values():
    assert set(OrderStatus) == {
        OrderStatus.READY,
        OrderStatus.SHIPPED,
        OrderStatus.BLOCKED,
        OrderStatus.CLOSED,
        OrderStatus.UNKNOWN,
        OrderStatus.REGISTERED,
    }


def test_order_status_string_values():
    assert OrderStatus.READY == "ready"
    assert OrderStatus.SHIPPED == "shipped"
    assert OrderStatus.BLOCKED == "blocked"
    assert OrderStatus.CLOSED == "closed"
    assert OrderStatus.UNKNOWN == "unknown"
    assert OrderStatus.REGISTERED == "registered"


def test_order_status_invalid_value_raises():
    with pytest.raises(ValueError):
        OrderStatus("pending")


# ---------------------------------------------------------------------------
# Stock
# ---------------------------------------------------------------------------


def test_stock_instantiation():
    s = Stock(wood_type=WoodType.OAK, quantity=10)
    assert s.wood_type == WoodType.OAK
    assert s.quantity == 10


def test_stock_invalid_wood_type_raises():
    with pytest.raises(ValidationError):
        Stock(wood_type="walnut", quantity=10)


def test_stock_invalid_quantity_raises():
    with pytest.raises(ValidationError):
        Stock(wood_type=WoodType.OAK, quantity="not-a-number")


def test_stock_to_json_round_trip():
    s = Stock(wood_type=WoodType.PINE, quantity=42)
    data = json.loads(s.to_json())
    assert data["wood_type"] == "pine"
    assert data["quantity"] == 42


def test_stock_model_dump():
    s = Stock(wood_type=WoodType.BIRCH, quantity=5)
    d = s.model_dump()
    assert d == {"wood_type": WoodType.BIRCH, "quantity": 5}


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------


def test_order_instantiation():
    o = Order(wood_type=WoodType.MAPLE, quantity=3)
    assert o.wood_type == WoodType.MAPLE
    assert o.quantity == 3


def test_order_invalid_wood_type_raises():
    with pytest.raises(ValidationError):
        Order(wood_type="teak", quantity=3)


def test_order_invalid_quantity_raises():
    with pytest.raises(ValidationError):
        Order(wood_type=WoodType.ELM, quantity=None)


def test_order_to_json_round_trip():
    o = Order(wood_type=WoodType.ELM, quantity=7)
    data = json.loads(o.to_json())
    assert data["wood_type"] == "elm"
    assert data["quantity"] == 7


def test_order_model_dump():
    o = Order(wood_type=WoodType.OAK, quantity=1)
    d = o.model_dump()
    assert d == {"wood_type": WoodType.OAK, "quantity": 1}


# ---------------------------------------------------------------------------
# OrderTracking
# ---------------------------------------------------------------------------

NOW = datetime(2026, 3, 15, 10, 0, 0)


def test_order_tracking_instantiation():
    ot = OrderTracking(
        id=1,
        order_status=OrderStatus.REGISTERED,
        wood_type=WoodType.OAK,
        quantity=10,
        date=NOW,
    )
    assert ot.id == 1
    assert ot.order_status == OrderStatus.REGISTERED
    assert ot.wood_type == WoodType.OAK
    assert ot.quantity == 10
    assert ot.date == NOW


def test_order_tracking_invalid_status_raises():
    with pytest.raises(ValidationError):
        OrderTracking(
            id=1,
            order_status="pending",
            wood_type=WoodType.OAK,
            quantity=10,
            date=NOW,
        )


def test_order_tracking_to_json_round_trip():
    ot = OrderTracking(
        id=42,
        order_status=OrderStatus.SHIPPED,
        wood_type=WoodType.MAPLE,
        quantity=5,
        date=NOW,
    )
    data = json.loads(ot.to_json())
    assert data["id"] == 42
    assert data["order_status"] == "shipped"
    assert data["wood_type"] == "maple"
    assert data["quantity"] == 5


def test_order_tracking_model_dump():
    ot = OrderTracking(
        id=99,
        order_status=OrderStatus.CLOSED,
        wood_type=WoodType.BIRCH,
        quantity=20,
        date=NOW,
    )
    d = ot.model_dump()
    assert d["id"] == 99
    assert d["order_status"] == OrderStatus.CLOSED
    assert d["wood_type"] == WoodType.BIRCH
    assert d["quantity"] == 20
    assert d["date"] == NOW
