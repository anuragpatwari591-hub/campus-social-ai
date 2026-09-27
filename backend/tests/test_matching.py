from tests.conftest import register_user


def _login(client, email, username, **kwargs):
    register_user(client, email=email, username=username, **kwargs)
    token = client.post("/api/auth/login", json={"email": email, "password": "Password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_candidates_returned_with_explainable_breakdown(client):
    headers_a = _login(client, "m1@campus.ai", "matcher1", interests=["coding", "music"])
    _login(client, "m2@campus.ai", "matcher2", interests=["coding", "gaming"])

    resp = client.get("/api/matching/candidates", params={"mode": "friendship"}, headers=headers_a)
    assert resp.status_code == 200
    candidates = resp.json()
    assert len(candidates) == 1
    candidate = candidates[0]
    assert 0 <= candidate["score_percent"] <= 100
    assert "interest_similarity" in candidate["score_breakdown"]
    assert "weights" in candidate["score_breakdown"]


def test_invalid_mode_rejected(client):
    headers = _login(client, "m3@campus.ai", "matcher3")
    resp = client.get("/api/matching/candidates", params={"mode": "not_a_real_mode"}, headers=headers)
    assert resp.status_code == 400


def test_dating_mode_requires_adult_verification(client):
    headers = _login(client, "m4@campus.ai", "matcher4")
    resp = client.get("/api/matching/candidates", params={"mode": "dating"}, headers=headers)
    assert resp.status_code == 403


def test_connect_decision_creates_connection(client):
    headers_a = _login(client, "m5@campus.ai", "matcher5", interests=["coding"])
    _login(client, "m6@campus.ai", "matcher6", interests=["coding"])

    candidates = client.get("/api/matching/candidates", params={"mode": "friendship"}, headers=headers_a).json()
    match_id = candidates[0]["match_id"]

    resp = client.post(f"/api/matching/{match_id}/decision", json={"decision": "connect"}, headers=headers_a)
    assert resp.status_code == 200

    connections = client.get("/api/matching/connections", headers=headers_a).json()
    assert len(connections) == 1
    assert connections[0]["status"] == "pending"
