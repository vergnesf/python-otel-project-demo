"""CRUD tests for ms-order Flask routes using SQLite in-memory database.

Fixtures: app (session-scoped, shared across all tests in this file),
client (function-scoped), clean_orders (autouse — deletes all rows before each test).

The conftest.py sets DATABASE_URL to a named shared-memory SQLite URI before any
module imports, ensuring both Flask-SQLAlchemy (db.create_all) and raw SessionLocal
(used in routes) connect to the same in-memory database.
"""

import pytest


@pytest.fixture(scope="module")
def app():
    from order import create_app

    return create_app()


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clean_orders(app):
    """Delete all orders before each test for isolation."""
    with app.app_context():
        from order.database import db
        from order.models import Order

        db.session.query(Order).delete()
        db.session.commit()
    yield


# ---------------------------------------------------------------------------
# POST /orders
# ---------------------------------------------------------------------------


def test_create_order_returns_201(client):
    response = client.post("/orders/", json={"wood_type": "oak", "quantity": 5})
    assert response.status_code == 201
    data = response.get_json()
    assert data["wood_type"] == "oak"
    assert data["quantity"] == 5
    assert "id" in data


def test_create_order_missing_body_returns_400(client):
    # Empty body with JSON content-type: Flask's request.json returns None → route returns 400.
    # The response body may be empty (no JSON payload) depending on how Flask handles the bad request.
    response = client.post("/orders/", data="", content_type="application/json")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /orders
# ---------------------------------------------------------------------------


def test_get_orders_returns_200_and_list(client):
    client.post("/orders/", json={"wood_type": "oak", "quantity": 3})
    response = client.get("/orders/")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
    assert len(response.get_json()) == 1


def test_get_orders_invalid_skip_returns_400(client):
    response = client.get("/orders/?skip=abc")
    assert response.status_code == 400
    assert "skip and limit must be integers" in response.get_json()["error"]


def test_get_orders_invalid_limit_returns_400(client):
    response = client.get("/orders/?limit=xyz")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /orders/status/<status>
# ---------------------------------------------------------------------------


def test_get_orders_by_status_registered_returns_200(client):
    client.post("/orders/", json={"wood_type": "maple", "quantity": 2})
    response = client.get("/orders/status/registered")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_get_orders_by_invalid_status_returns_400(client):
    response = client.get("/orders/status/nonexistent")
    assert response.status_code == 400
    assert "Invalid status" in response.get_json()["error"]


# ---------------------------------------------------------------------------
# PUT /orders/<id>
# ---------------------------------------------------------------------------


def test_update_order_status_returns_200(client):
    create_resp = client.post("/orders/", json={"wood_type": "birch", "quantity": 1})
    order_id = create_resp.get_json()["id"]
    response = client.put(f"/orders/{order_id}", json={"order_status": "shipped"})
    assert response.status_code == 200
    assert response.get_json()["order_status"] == "shipped"


def test_update_order_status_invalid_status_returns_400(client):
    create_resp = client.post("/orders/", json={"wood_type": "pine", "quantity": 1})
    order_id = create_resp.get_json()["id"]
    response = client.put(f"/orders/{order_id}", json={"order_status": "invalid_status"})
    assert response.status_code == 400


def test_update_order_status_missing_body_returns_400(client):
    create_resp = client.post("/orders/", json={"wood_type": "elm", "quantity": 1})
    order_id = create_resp.get_json()["id"]
    response = client.put(f"/orders/{order_id}", data="", content_type="application/json")
    assert response.status_code == 400


def test_update_order_status_not_found_returns_404(client):
    response = client.put("/orders/99999", json={"order_status": "shipped"})
    assert response.status_code == 404
