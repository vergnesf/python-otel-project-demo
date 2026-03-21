"""Unit tests for lib_models.models — shared Pydantic v2 data contracts (brewery domain).

Coverage:
- IngredientType enum: all 5 values, invalid value rejection
- BrewStatus enum: all 7 values (including BREWING), invalid value rejection
- BrewStyle enum: all 4 values, invalid value rejection
- IngredientStock: instantiation, type validation, model_dump_json() round-trip
- BrewOrder: instantiation, brew_style field, validation, model_dump_json() round-trip
- BrewTracking: instantiation with datetime, all fields, model_dump_json()
- InsufficientIngredientError, IngredientNotFoundError: raise correctly
"""

import json
from datetime import datetime

import pytest
from lib_models.models import BrewOrder, BrewStatus, BrewStyle, BrewTracking, IngredientNotFoundError, IngredientStock, IngredientType, InsufficientIngredientError
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# IngredientType
# ---------------------------------------------------------------------------


def test_ingredient_type_all_values():
    assert set(IngredientType) == {
        IngredientType.MALT,
        IngredientType.HOPS,
        IngredientType.YEAST,
        IngredientType.WHEAT,
        IngredientType.BARLEY,
    }


def test_ingredient_type_string_values():
    assert IngredientType.MALT == "malt"
    assert IngredientType.HOPS == "hops"
    assert IngredientType.YEAST == "yeast"
    assert IngredientType.WHEAT == "wheat"
    assert IngredientType.BARLEY == "barley"


def test_ingredient_type_invalid_value_raises():
    with pytest.raises(ValueError):
        IngredientType("oak")


# ---------------------------------------------------------------------------
# BrewStatus
# ---------------------------------------------------------------------------


def test_brew_status_all_values():
    assert set(BrewStatus) == {
        BrewStatus.REGISTERED,
        BrewStatus.BREWING,
        BrewStatus.READY,
        BrewStatus.SHIPPED,
        BrewStatus.BLOCKED,
        BrewStatus.CLOSED,
        BrewStatus.UNKNOWN,
    }


def test_brew_status_string_values():
    assert BrewStatus.REGISTERED == "registered"
    assert BrewStatus.BREWING == "brewing"
    assert BrewStatus.READY == "ready"
    assert BrewStatus.SHIPPED == "shipped"
    assert BrewStatus.BLOCKED == "blocked"
    assert BrewStatus.CLOSED == "closed"
    assert BrewStatus.UNKNOWN == "unknown"


def test_brew_status_invalid_value_raises():
    with pytest.raises(ValueError):
        BrewStatus("pending")


# ---------------------------------------------------------------------------
# BrewStyle
# ---------------------------------------------------------------------------


def test_brew_style_all_values():
    assert set(BrewStyle) == {
        BrewStyle.LAGER,
        BrewStyle.IPA,
        BrewStyle.STOUT,
        BrewStyle.WHEAT_BEER,
    }


def test_brew_style_string_values():
    assert BrewStyle.LAGER == "lager"
    assert BrewStyle.IPA == "ipa"
    assert BrewStyle.STOUT == "stout"
    assert BrewStyle.WHEAT_BEER == "wheat_beer"


def test_brew_style_invalid_value_raises():
    with pytest.raises(ValueError):
        BrewStyle("pilsner")


# ---------------------------------------------------------------------------
# IngredientStock
# ---------------------------------------------------------------------------


def test_ingredient_stock_instantiation():
    s = IngredientStock(ingredient_type=IngredientType.MALT, quantity=100)
    assert s.ingredient_type == IngredientType.MALT
    assert s.quantity == 100


def test_ingredient_stock_invalid_type_raises():
    with pytest.raises(ValidationError):
        IngredientStock(ingredient_type="oak", quantity=10)


def test_ingredient_stock_invalid_quantity_raises():
    with pytest.raises(ValidationError):
        IngredientStock(ingredient_type=IngredientType.HOPS, quantity="not-a-number")


def test_ingredient_stock_zero_quantity_raises():
    with pytest.raises(ValidationError):
        IngredientStock(ingredient_type=IngredientType.HOPS, quantity=0)


def test_ingredient_stock_negative_quantity_raises():
    with pytest.raises(ValidationError):
        IngredientStock(ingredient_type=IngredientType.HOPS, quantity=-1)


def test_ingredient_stock_json_round_trip():
    s = IngredientStock(ingredient_type=IngredientType.YEAST, quantity=42)
    data = json.loads(s.model_dump_json())
    assert data["ingredient_type"] == "yeast"
    assert data["quantity"] == 42


def test_ingredient_stock_model_dump():
    s = IngredientStock(ingredient_type=IngredientType.WHEAT, quantity=5)
    d = s.model_dump()
    assert d == {"ingredient_type": IngredientType.WHEAT, "quantity": 5}


# ---------------------------------------------------------------------------
# BrewOrder
# ---------------------------------------------------------------------------


def test_brew_order_instantiation():
    o = BrewOrder(ingredient_type=IngredientType.MALT, quantity=3, brew_style=BrewStyle.IPA)
    assert o.ingredient_type == IngredientType.MALT
    assert o.quantity == 3
    assert o.brew_style == BrewStyle.IPA


def test_brew_order_invalid_ingredient_type_raises():
    with pytest.raises(ValidationError):
        BrewOrder(ingredient_type="wood", quantity=3, brew_style=BrewStyle.LAGER)


def test_brew_order_invalid_brew_style_raises():
    with pytest.raises(ValidationError):
        BrewOrder(ingredient_type=IngredientType.HOPS, quantity=3, brew_style="pilsner")


def test_brew_order_invalid_quantity_raises():
    with pytest.raises(ValidationError):
        BrewOrder(ingredient_type=IngredientType.BARLEY, quantity=None, brew_style=BrewStyle.STOUT)


def test_brew_order_zero_quantity_raises():
    with pytest.raises(ValidationError):
        BrewOrder(ingredient_type=IngredientType.BARLEY, quantity=0, brew_style=BrewStyle.STOUT)


def test_brew_order_negative_quantity_raises():
    with pytest.raises(ValidationError):
        BrewOrder(ingredient_type=IngredientType.BARLEY, quantity=-5, brew_style=BrewStyle.STOUT)


def test_brew_order_json_round_trip():
    o = BrewOrder(ingredient_type=IngredientType.HOPS, quantity=7, brew_style=BrewStyle.STOUT)
    data = json.loads(o.model_dump_json())
    assert data["ingredient_type"] == "hops"
    assert data["quantity"] == 7
    assert data["brew_style"] == "stout"


def test_brew_order_model_dump():
    o = BrewOrder(ingredient_type=IngredientType.MALT, quantity=1, brew_style=BrewStyle.WHEAT_BEER)
    d = o.model_dump()
    assert d == {"ingredient_type": IngredientType.MALT, "quantity": 1, "brew_style": BrewStyle.WHEAT_BEER}


# ---------------------------------------------------------------------------
# BrewTracking
# ---------------------------------------------------------------------------

NOW = datetime(2026, 3, 21, 10, 0, 0)


def test_brew_tracking_instantiation():
    bt = BrewTracking(
        id=1,
        brew_status=BrewStatus.REGISTERED,
        ingredient_type=IngredientType.MALT,
        quantity=10,
        brew_style=BrewStyle.LAGER,
        date=NOW,
    )
    assert bt.id == 1
    assert bt.brew_status == BrewStatus.REGISTERED
    assert bt.ingredient_type == IngredientType.MALT
    assert bt.quantity == 10
    assert bt.brew_style == BrewStyle.LAGER
    assert bt.date == NOW


def test_brew_tracking_brewing_status():
    bt = BrewTracking(
        id=2,
        brew_status=BrewStatus.BREWING,
        ingredient_type=IngredientType.HOPS,
        quantity=5,
        brew_style=BrewStyle.IPA,
        date=NOW,
    )
    assert bt.brew_status == BrewStatus.BREWING


def test_brew_tracking_invalid_status_raises():
    with pytest.raises(ValidationError):
        BrewTracking(
            id=1,
            brew_status="pending",
            ingredient_type=IngredientType.MALT,
            quantity=10,
            brew_style=BrewStyle.LAGER,
            date=NOW,
        )


def test_brew_tracking_json_round_trip():
    bt = BrewTracking(
        id=42,
        brew_status=BrewStatus.SHIPPED,
        ingredient_type=IngredientType.YEAST,
        quantity=5,
        brew_style=BrewStyle.STOUT,
        date=NOW,
    )
    data = json.loads(bt.model_dump_json())
    assert data["id"] == 42
    assert data["brew_status"] == "shipped"
    assert data["ingredient_type"] == "yeast"
    assert data["brew_style"] == "stout"
    assert data["quantity"] == 5


def test_brew_tracking_model_dump():
    bt = BrewTracking(
        id=99,
        brew_status=BrewStatus.CLOSED,
        ingredient_type=IngredientType.WHEAT,
        quantity=20,
        brew_style=BrewStyle.WHEAT_BEER,
        date=NOW,
    )
    d = bt.model_dump()
    assert d["id"] == 99
    assert d["brew_status"] == BrewStatus.CLOSED
    assert d["ingredient_type"] == IngredientType.WHEAT
    assert d["brew_style"] == BrewStyle.WHEAT_BEER
    assert d["quantity"] == 20
    assert d["date"] == NOW


# ---------------------------------------------------------------------------
# BrewTracking — negative quantity
# ---------------------------------------------------------------------------


def test_brew_tracking_negative_quantity_raises():
    with pytest.raises(ValidationError):
        BrewTracking(
            id=1,
            brew_status=BrewStatus.REGISTERED,
            ingredient_type=IngredientType.MALT,
            quantity=-1,
            brew_style=BrewStyle.LAGER,
            date=NOW,
        )


def test_brew_tracking_zero_quantity_raises():
    with pytest.raises(ValidationError):
        BrewTracking(
            id=1,
            brew_status=BrewStatus.REGISTERED,
            ingredient_type=IngredientType.MALT,
            quantity=0,
            brew_style=BrewStyle.LAGER,
            date=NOW,
        )


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


def test_insufficient_ingredient_error_raises():
    with pytest.raises(InsufficientIngredientError):
        raise InsufficientIngredientError("malt", requested=10, available=3)


def test_insufficient_ingredient_error_payload():
    err = InsufficientIngredientError("hops", requested=20, available=5)
    assert err.ingredient_type == "hops"
    assert err.requested == 20
    assert err.available == 5
    assert "hops" in str(err)
    assert "20" in str(err)
    assert "5" in str(err)


def test_ingredient_not_found_error_raises():
    with pytest.raises(IngredientNotFoundError):
        raise IngredientNotFoundError("yeast")


def test_ingredient_not_found_error_payload():
    err = IngredientNotFoundError("barley")
    assert err.ingredient_type == "barley"
    assert "barley" in str(err)


def test_insufficient_ingredient_error_is_exception():
    assert issubclass(InsufficientIngredientError, Exception)


def test_ingredient_not_found_error_is_exception():
    assert issubclass(IngredientNotFoundError, Exception)
