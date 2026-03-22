"""CRUD tests for ms-beerstock Flask routes using SQLite in-memory database.

Fixtures: app (module-scoped, shared across all tests in this file),
client (function-scoped), clean_stocks (autouse — deletes all rows before each test).

The conftest.py sets DATABASE_URL to a temp SQLite file before any module imports,
ensuring both Flask-SQLAlchemy (db.create_all) and raw SessionLocal (used in routes)
connect to the same physical database.
"""

import pytest


@pytest.fixture(scope="module")
def app():
    from beerstock import create_app

    return create_app()


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clean_stocks(app):
    """Delete all beer stocks before each test for isolation."""
    with app.app_context():
        from beerstock.database import db
        from beerstock.models import BeerStockModel

        db.session.query(BeerStockModel).delete()
        db.session.commit()
    yield


# ---------------------------------------------------------------------------
# POST /beerstock
# ---------------------------------------------------------------------------


def test_create_beer_stock_returns_201(client):
    response = client.post("/beerstock/", json={"brew_style": "ipa", "quantity": 50})
    assert response.status_code == 201
    data = response.get_json()
    assert data["brew_style"] == "ipa"
    assert data["quantity"] == 50


def test_create_beer_stock_missing_body_returns_400(client):
    response = client.post("/beerstock/", data="", content_type="application/json")
    assert response.status_code == 400


def test_create_beer_stock_same_style_accumulates(client):
    """Creating stock with same brew style should accumulate quantity."""
    client.post("/beerstock/", json={"brew_style": "lager", "quantity": 10})
    client.post("/beerstock/", json={"brew_style": "lager", "quantity": 5})
    response = client.get("/beerstock/lager")
    assert response.status_code == 200
    assert response.get_json()["quantity"] == 15


# ---------------------------------------------------------------------------
# GET /beerstock
# ---------------------------------------------------------------------------


def test_get_beer_stocks_returns_200_and_list(client):
    client.post("/beerstock/", json={"brew_style": "stout", "quantity": 20})
    response = client.get("/beerstock/")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
    assert len(response.get_json()) == 1


def test_get_beer_stocks_invalid_skip_returns_400(client):
    response = client.get("/beerstock/?skip=abc")
    assert response.status_code == 400
    assert "skip and limit must be integers" in response.get_json()["error"]


def test_get_beer_stocks_invalid_limit_returns_400(client):
    response = client.get("/beerstock/?limit=xyz")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /beerstock/<brew_style>
# ---------------------------------------------------------------------------


def test_get_beer_stock_by_style_returns_200(client):
    client.post("/beerstock/", json={"brew_style": "wheat_beer", "quantity": 30})
    response = client.get("/beerstock/wheat_beer")
    assert response.status_code == 200
    assert response.get_json()["brew_style"] == "wheat_beer"


def test_get_beer_stock_by_style_not_found_returns_404(client):
    response = client.get("/beerstock/ipa")
    assert response.status_code == 404


def test_get_beer_stock_invalid_style_returns_400(client):
    response = client.get("/beerstock/pilsner")
    assert response.status_code == 400
    assert "Invalid brew style" in response.get_json()["error"]


# ---------------------------------------------------------------------------
# POST /beerstock/ship
# ---------------------------------------------------------------------------


def test_ship_beer_stock_returns_200(client):
    client.post("/beerstock/", json={"brew_style": "stout", "quantity": 100})
    response = client.post("/beerstock/ship", json={"brew_style": "stout", "quantity": 10})
    assert response.status_code == 200
    assert response.get_json()["quantity"] == 90


def test_ship_beer_stock_insufficient_returns_400(client):
    client.post("/beerstock/", json={"brew_style": "ipa", "quantity": 5})
    response = client.post("/beerstock/ship", json={"brew_style": "ipa", "quantity": 100})
    assert response.status_code == 400
    assert "Insufficient" in response.get_json()["error"]


def test_ship_beer_stock_not_found_returns_400(client):
    response = client.post("/beerstock/ship", json={"brew_style": "lager", "quantity": 1})
    assert response.status_code == 400


def test_ship_beer_stock_missing_body_returns_400(client):
    response = client.post("/beerstock/ship", data="", content_type="application/json")
    assert response.status_code == 400
