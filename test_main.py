from fastapi.testclient import TestClient
from DigiApi import app

client = TestClient(app)

# Helper function to register a user
def register_user(username="Hari", password="idealboy"):
    response = client.post("/register", json={"username": username, "password": password})
    return response

# Helper function to login and get the access token
def login_user(username="Hari", password="idealboy"):
    response = client.post("/login", json={"username": username, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_expenses_with_auth():
    # Step 1: Register user (ignore failure if user already exists)
    register_user()
    
    # Step 2: Login and get token
    token = login_user()
    assert token is not None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test GET /expenses/ with token
    response = client.get("/expenses/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Test POST /expenses/ with token
    payload = {
        "title": "Test Expense",
        "amount": 100,
        "category": "Testing",
        "date": "2025-05-25"
    }
    response = client.post("/expenses/", json=payload, headers=headers)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["amount"] == payload["amount"]
    assert data["category"] == payload["category"]
    assert data["date"] == payload["date"]
