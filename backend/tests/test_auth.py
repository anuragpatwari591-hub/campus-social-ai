from tests.conftest import register_user


def test_register_and_login(client):
    resp = register_user(client, interests=["coding", "music"])
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["username"] == "testuser"
    assert "access_token" in body

    login_resp = client.post("/api/auth/login", json={"email": "test@campus.ai", "password": "Password123"})
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_duplicate_email_rejected(client):
    register_user(client, email="dup@campus.ai", username="dupuser1")
    resp = register_user(client, email="dup@campus.ai", username="dupuser2")
    assert resp.status_code == 400


def test_duplicate_username_rejected(client):
    register_user(client, email="a1@campus.ai", username="sameuser")
    resp = register_user(client, email="a2@campus.ai", username="sameuser")
    assert resp.status_code == 400


def test_weak_password_rejected(client):
    resp = register_user(client, password="weak")
    assert resp.status_code == 422


def test_invalid_login_wrong_password(client):
    register_user(client)
    resp = client.post("/api/auth/login", json={"email": "test@campus.ai", "password": "WrongPass123"})
    assert resp.status_code == 401


def test_invalid_login_unknown_email(client):
    resp = client.post("/api/auth/login", json={"email": "nouser@campus.ai", "password": "Password123"})
    assert resp.status_code == 401


def test_me_requires_authentication(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client):
    register_user(client)
    login = client.post("/api/auth/login", json={"email": "test@campus.ai", "password": "Password123"}).json()
    token = login["access_token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"
