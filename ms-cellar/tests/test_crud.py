"""CRUD tests for ms-cellar Flask routes using SQLite in-memory database.

Fixtures: app (module-scoped, shared across all tests in this file),
client (function-scoped), clean_ingredients (autouse — deletes all rows before each test).

The conftest.py sets DATABASE_URL to a temp SQLite file before any module imports,
ensuring both Flask-SQLAlchemy (db.create_all) and raw SessionLocal (used in routes)
connect to the same physical database.
"""

import pytest


@pytest.fixture(scope="module")
def app():
    from cellar import create_app

    return create_app()


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clean_ingredients(app):
    """Delete all ingredient stocks before each test for isolation."""
    with app.app_context():
        from cellar.database import db
        from cellar.models import IngredientStockModel

        db.session.query(IngredientStockModel).delete()
        db.session.commit()
    yield


# ---------------------------------------------------------------------------
# POST /ingredients
# ---------------------------------------------------------------------------


def test_create_ingredient_returns_201(client):
    response = client.post("/ingredients/", json={"ingredient_type": "malt", "quantity": 50})
    assert response.status_code == 201
    data = response.get_json()
    assert data["ingredient_type"] == "malt"
    assert data["quantity"] == 50


def test_create_ingredient_missing_body_returns_400(client):
    response = client.post("/ingredients/", data="", content_type="application/json")
    assert response.status_code == 400


def test_create_ingredient_same_type_accumulates(client):
    """Creating stock with same ingredient type should accumulate quantity."""
    client.post("/ingredients/", json={"ingredient_type": "hops", "quantity": 10})
    client.post("/ingredients/", json={"ingredient_type": "hops", "quantity": 5})
    response = client.get("/ingredients/hops")
    assert response.status_code == 200
    assert response.get_json()["quantity"] == 15


# ---------------------------------------------------------------------------
# GET /ingredients
# ---------------------------------------------------------------------------


def test_get_ingredients_returns_200_and_list(client):
    client.post("/ingredients/", json={"ingredient_type": "yeast", "quantity": 20})
    response = client.get("/ingredients/")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
    assert len(response.get_json()) == 1


def test_get_ingredients_invalid_skip_returns_400(client):
    response = client.get("/ingredients/?skip=abc")
    assert response.status_code == 400
    assert "skip and limit must be integers" in response.get_json()["error"]


def test_get_ingredients_invalid_limit_returns_400(client):
    response = client.get("/ingredients/?limit=xyz")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /ingredients/<ingredient_type>
# ---------------------------------------------------------------------------


def test_get_ingredient_by_type_returns_200(client):
    client.post("/ingredients/", json={"ingredient_type": "wheat", "quantity": 30})
    response = client.get("/ingredients/wheat")
    assert response.status_code == 200
    assert response.get_json()["ingredient_type"] == "wheat"


def test_get_ingredient_by_type_not_found_returns_404(client):
    response = client.get("/ingredients/malt")
    assert response.status_code == 404


def test_get_ingredient_invalid_type_returns_400(client):
    response = client.get("/ingredients/oak")
    assert response.status_code == 400
    assert "Invalid ingredient type" in response.get_json()["error"]


# ---------------------------------------------------------------------------
# POST /ingredients/decrease
# ---------------------------------------------------------------------------


def test_decrease_ingredient_returns_200(client):
    client.post("/ingredients/", json={"ingredient_type": "barley", "quantity": 100})
    response = client.post("/ingredients/decrease", json={"ingredient_type": "barley", "quantity": 10})
    assert response.status_code == 200
    assert response.get_json()["quantity"] == 90


def test_decrease_ingredient_insufficient_returns_400(client):
    client.post("/ingredients/", json={"ingredient_type": "malt", "quantity": 5})
    response = client.post("/ingredients/decrease", json={"ingredient_type": "malt", "quantity": 100})
    assert response.status_code == 400
    assert "Insufficient" in response.get_json()["error"]


def test_decrease_ingredient_not_found_returns_404(client):
    response = client.post("/ingredients/decrease", json={"ingredient_type": "hops", "quantity": 1})
    assert response.status_code == 404


def test_decrease_ingredient_missing_body_returns_400(client):
    response = client.post("/ingredients/decrease", data="", content_type="application/json")
    assert response.status_code == 400
