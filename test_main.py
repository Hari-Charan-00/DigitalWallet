from fastapi.testclient import TestClient
from DigiApi import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200

def test_add_expense():
    payload = {
        "title": "Test Expense",
        "amount": 100,
        "category": "Testing",
        "date": "2025-05-25"
    }
    response = client.post("/expenses/", json=payload)
    assert response.status_code == 200 or response.status_code == 201
