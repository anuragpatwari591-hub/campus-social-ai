from tests.conftest import register_user


def _auth_headers(client):
    register_user(client, email="ai@campus.ai", username="aiuser")
    token = client.post("/api/auth/login", json={"email": "ai@campus.ai", "password": "Password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_ai_text_generation_mock_provider(client):
    headers = _auth_headers(client)
    resp = client.post("/api/ai/text", json={"prompt": "college fest tomorrow", "style": "funny"}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["text"], str) and len(body["text"]) > 0


def test_ai_text_empty_prompt_rejected(client):
    headers = _auth_headers(client)
    resp = client.post("/api/ai/text", json={"prompt": "   "}, headers=headers)
    assert resp.status_code == 422


def test_ai_image_generation_returns_url(client):
    headers = _auth_headers(client)
    resp = client.post("/api/ai/image", json={"prompt": "futuristic college fest poster"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["image_url"].startswith("http")


def test_ai_requires_authentication(client):
    resp = client.post("/api/ai/text", json={"prompt": "hello"})
    assert resp.status_code == 401


def test_ai_moderation_blocks_flagged_generated_text(client, monkeypatch):
    headers = _auth_headers(client)
    from app.ai.mock_provider import MockAIProvider
    monkeypatch.setattr(MockAIProvider, "generate_text", lambda self, prompt, style="casual", max_words=60: "call me at 9876543210")
    resp = client.post("/api/ai/text", json={"prompt": "share my number"}, headers=headers)
    assert resp.status_code == 422


def test_campus_assistant_labels_source(client):
    headers = _auth_headers(client)
    resp = client.post("/api/ai/assistant", json={"prompt": "what events are happening this week?"}, headers=headers)
    assert resp.status_code == 200
    assert "source" in resp.json()
