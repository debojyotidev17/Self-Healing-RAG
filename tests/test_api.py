import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_api_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "operational"

def test_api_ask_validation_error():
    # Empty question should return 422 Unprocessable Entity
    res = client.post("/ask", json={"question": "   ", "max_retries": 2})
    assert res.status_code == 422

def test_api_ask_success():
    res = client.post("/ask", json={"question": "What is the equipment stipend for new hires?", "max_retries": 2, "use_cache": False})
    assert res.status_code == 200
    data = res.json()
    assert "final_response" in data
    assert "grounded" in data
    assert "citations" in data
    assert "trace" in data
