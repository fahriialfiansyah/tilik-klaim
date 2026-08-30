from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_reports_ok_and_engine_identity():
    # Arrange / Act
    response = client.get("/healthz")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["data_class"] == "synthetic"
    assert "engine_version" in body
    assert "ruleset_version" in body
