from fastapi.testclient import TestClient
from services.api_gateway.app.main import app

client = TestClient(app)

def test_health_check():
    """Tests if the health check endpoint is working correctly."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}