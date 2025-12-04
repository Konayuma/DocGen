"""
Integration tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from docgen.main import app


@pytest.fixture
def client():
    """Fixture for test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_info(client):
    """Test API info endpoint."""
    response = client.get("/api/info")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "max_file_size_mb" in data


def test_index_page(client):
    """Test main index page loads."""
    response = client.get("/")
    assert response.status_code == 200
    assert "DocGen" in response.text
    assert "Upload" in response.text
