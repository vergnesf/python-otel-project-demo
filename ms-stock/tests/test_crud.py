"""CRUD tests for ms-stock Flask routes using SQLite in-memory database.

Fixtures: app (session-scoped, shared across all tests in this file),
client (function-scoped), clean_stocks (autouse — deletes all rows before each test).

The conftest.py sets DATABASE_URL to a temp SQLite file before any module imports,
ensuring both Flask-SQLAlchemy (db.create_all) and raw SessionLocal (used in routes)
connect to the same physical database.
"""

import pytest


@pytest.fixture(scope="module")
def app():
    from stock import create_app

    return create_app()


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clean_stocks(app):
    """Delete all stocks before each test for isolation."""
    with app.app_context():
        from stock.database import db
        from stock.models import Stock

        db.session.query(Stock).delete()
        db.session.commit()
    yield


# ---------------------------------------------------------------------------
# POST /stocks
# ---------------------------------------------------------------------------


def test_create_stock_returns_201(client):
    response = client.post("/stocks/", json={"wood_type": "oak", "quantity": 50})
    assert response.status_code == 201
    data = response.get_json()
    assert data["wood_type"] == "oak"
    assert data["quantity"] == 50
    # Stock uses wood_type as PK — no separate id field


def test_create_stock_missing_body_returns_400(client):
    response = client.post("/stocks/", data="", content_type="application/json")
    assert response.status_code == 400


def test_create_stock_same_wood_type_accumulates(client):
    """Creating stock with same wood type should accumulate quantity."""
    client.post("/stocks/", json={"wood_type": "maple", "quantity": 10})
    client.post("/stocks/", json={"wood_type": "maple", "quantity": 5})
    response = client.get("/stocks/maple")
    assert response.status_code == 200
    assert response.get_json()["quantity"] == 15


# ---------------------------------------------------------------------------
# GET /stocks
# ---------------------------------------------------------------------------


def test_get_stocks_returns_200_and_list(client):
    client.post("/stocks/", json={"wood_type": "birch", "quantity": 20})
    response = client.get("/stocks/")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
    assert len(response.get_json()) == 1


def test_get_stocks_invalid_skip_returns_400(client):
    response = client.get("/stocks/?skip=abc")
    assert response.status_code == 400
    assert "skip and limit must be integers" in response.get_json()["error"]


def test_get_stocks_invalid_limit_returns_400(client):
    response = client.get("/stocks/?limit=xyz")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /stocks/<wood_type>
# ---------------------------------------------------------------------------


def test_get_stock_by_wood_type_returns_200(client):
    client.post("/stocks/", json={"wood_type": "pine", "quantity": 30})
    response = client.get("/stocks/pine")
    assert response.status_code == 200
    assert response.get_json()["wood_type"] == "pine"


def test_get_stock_by_wood_type_not_found_returns_404(client):
    response = client.get("/stocks/elm")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /stocks/decrease
# ---------------------------------------------------------------------------


def test_decrease_stock_returns_200(client):
    client.post("/stocks/", json={"wood_type": "oak", "quantity": 100})
    response = client.post("/stocks/decrease", json={"wood_type": "oak", "quantity": 10})
    assert response.status_code == 200
    assert response.get_json()["quantity"] == 90


def test_decrease_stock_insufficient_returns_400(client):
    client.post("/stocks/", json={"wood_type": "maple", "quantity": 5})
    response = client.post("/stocks/decrease", json={"wood_type": "maple", "quantity": 100})
    assert response.status_code == 400
    assert "Insufficient" in response.get_json()["error"]


def test_decrease_stock_not_found_returns_404(client):
    response = client.post("/stocks/decrease", json={"wood_type": "birch", "quantity": 1})
    assert response.status_code == 404


def test_decrease_stock_missing_body_returns_400(client):
    response = client.post("/stocks/decrease", data="", content_type="application/json")
    assert response.status_code == 400
