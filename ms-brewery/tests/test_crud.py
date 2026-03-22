"""CRUD tests for ms-brewery Flask routes using SQLite in-memory database.

Fixtures: app (session-scoped, shared across all tests in this file),
client (function-scoped), clean_brews (autouse — deletes all rows before each test).

The conftest.py sets DATABASE_URL to a named shared-memory SQLite URI before any
module imports, ensuring both Flask-SQLAlchemy (db.create_all) and raw SessionLocal
(used in routes) connect to the same in-memory database.
"""

import pytest


@pytest.fixture(scope="module")
def app():
    from brewery import create_app

    return create_app()


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clean_brews(app):
    """Delete all brews before each test for isolation."""
    with app.app_context():
        from brewery.database import db
        from brewery.models import BrewModel

        db.session.query(BrewModel).delete()
        db.session.commit()
    yield


# ---------------------------------------------------------------------------
# POST /brews
# ---------------------------------------------------------------------------


def test_create_brew_returns_201(client):
    response = client.post("/brews/", json={"ingredient_type": "malt", "quantity": 5, "brew_style": "lager"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["ingredient_type"] == "malt"
    assert data["quantity"] == 5
    assert data["brew_style"] == "lager"
    assert data["brew_status"] == "registered"
    assert "id" in data


def test_create_brew_missing_body_returns_400(client):
    # Empty body with JSON content-type: Flask's request.json returns None → route returns 400.
    response = client.post("/brews/", data="", content_type="application/json")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /brews
# ---------------------------------------------------------------------------


def test_get_brews_returns_200_and_list(client):
    client.post("/brews/", json={"ingredient_type": "hops", "quantity": 3, "brew_style": "ipa"})
    response = client.get("/brews/")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
    assert len(response.get_json()) == 1


def test_get_brews_invalid_skip_returns_400(client):
    response = client.get("/brews/?skip=abc")
    assert response.status_code == 400
    assert "skip and limit must be integers" in response.get_json()["error"]


def test_get_brews_invalid_limit_returns_400(client):
    response = client.get("/brews/?limit=xyz")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /brews/status/<status>
# ---------------------------------------------------------------------------


def test_get_brews_by_status_registered_returns_200(client):
    client.post("/brews/", json={"ingredient_type": "yeast", "quantity": 2, "brew_style": "stout"})
    response = client.get("/brews/status/registered")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_get_brews_by_invalid_status_returns_400(client):
    response = client.get("/brews/status/nonexistent")
    assert response.status_code == 400
    assert "Invalid status" in response.get_json()["error"]


# ---------------------------------------------------------------------------
# PUT /brews/<id>
# ---------------------------------------------------------------------------


def test_update_brew_status_returns_200(client):
    create_resp = client.post("/brews/", json={"ingredient_type": "barley", "quantity": 1, "brew_style": "wheat_beer"})
    brew_id = create_resp.get_json()["id"]
    response = client.put(f"/brews/{brew_id}", json={"brew_status": "shipped"})
    assert response.status_code == 200
    assert response.get_json()["brew_status"] == "shipped"


def test_update_brew_status_invalid_status_returns_400(client):
    create_resp = client.post("/brews/", json={"ingredient_type": "malt", "quantity": 1, "brew_style": "lager"})
    brew_id = create_resp.get_json()["id"]
    response = client.put(f"/brews/{brew_id}", json={"brew_status": "invalid_status"})
    assert response.status_code == 400


def test_update_brew_status_missing_body_returns_400(client):
    create_resp = client.post("/brews/", json={"ingredient_type": "hops", "quantity": 1, "brew_style": "ipa"})
    brew_id = create_resp.get_json()["id"]
    response = client.put(f"/brews/{brew_id}", data="", content_type="application/json")
    assert response.status_code == 400


def test_update_brew_status_not_found_returns_404(client):
    response = client.put("/brews/99999", json={"brew_status": "shipped"})
    assert response.status_code == 404


def test_update_brew_status_ready_publishes_to_kafka(client):
    """Transitioning to READY must call publish_brew_ready exactly once."""
    from unittest.mock import patch

    create_resp = client.post("/brews/", json={"ingredient_type": "malt", "quantity": 1, "brew_style": "ipa"})
    brew_id = create_resp.get_json()["id"]

    with patch("brewery.routes.brews.publish_brew_ready") as mock_publish:
        response = client.put(f"/brews/{brew_id}", json={"brew_status": "ready"})

    assert response.status_code == 200
    assert response.get_json()["brew_status"] == "ready"
    mock_publish.assert_called_once()
    assert mock_publish.call_args.args[0]["id"] == brew_id


def test_update_brew_status_non_ready_does_not_publish(client):
    """Transitioning to a non-READY status must NOT call publish_brew_ready."""
    from unittest.mock import patch

    create_resp = client.post("/brews/", json={"ingredient_type": "hops", "quantity": 1, "brew_style": "stout"})
    brew_id = create_resp.get_json()["id"]

    with patch("brewery.routes.brews.publish_brew_ready") as mock_publish:
        response = client.put(f"/brews/{brew_id}", json={"brew_status": "shipped"})

    assert response.status_code == 200
    mock_publish.assert_not_called()
