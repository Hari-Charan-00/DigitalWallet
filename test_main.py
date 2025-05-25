# test_digiapi.py

from fastapi.testclient import TestClient
from DigiApi import app

client = TestClient(app)

def test_get_expenses():
    """Test retrieving expenses (GET request)"""
    response = client.get("/expenses/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # Optional, checks if the response is a list

def test_add_expense():
    """Test adding a new expense (POST request)"""
    payload = {
        "title": "Test Expense",
        "amount": 100,
        "category": "Testing",
        "date": "2025-05-25"
    }
    response = client.post("/expenses/", json=payload)
    assert response.status_code in [200, 201]  # Accept either 200 OK or 201 Created
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["amount"] == payload["amount"]
    assert data["category"] == payload["category"]
    assert data["date"] == payload["date"]
