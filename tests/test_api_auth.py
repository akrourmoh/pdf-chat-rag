"""Integration tests for the authentication endpoints."""


def test_register_login_and_me(client):
    r = client.post("/register", json={"email": "auth1@test.com", "password": "password123"})
    assert r.status_code == 201
    assert r.json()["email"] == "auth1@test.com"

    r = client.post("/login", data={"username": "auth1@test.com", "password": "password123"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "auth1@test.com"


def test_duplicate_email_rejected(client):
    client.post("/register", json={"email": "dup@test.com", "password": "password123"})
    r = client.post("/register", json={"email": "dup@test.com", "password": "password123"})
    assert r.status_code == 400


def test_short_password_rejected(client):
    r = client.post("/register", json={"email": "short@test.com", "password": "123"})
    assert r.status_code == 400


def test_wrong_password_rejected(client):
    client.post("/register", json={"email": "wrong@test.com", "password": "password123"})
    r = client.post("/login", data={"username": "wrong@test.com", "password": "BADPASS"})
    assert r.status_code == 401


def test_protected_routes_require_token(client):
    assert client.get("/me").status_code == 401
    assert client.post("/ask", json={"question": "hi"}).status_code == 401
    assert client.get("/status").status_code == 401
