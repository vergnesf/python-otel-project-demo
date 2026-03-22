"""Smoke tests for beerstock service — verify Flask app starts and health endpoint responds."""

import pytest


@pytest.fixture
def app():
    from beerstock import create_app

    return create_app()


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None, f"Expected JSON response, got Content-Type: {response.content_type}"
    assert data["status"] == "healthy"
