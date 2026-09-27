from tests.conftest import register_user


def _auth_headers(client, email="poster@campus.ai", username="poster"):
    register_user(client, email=email, username=username)
    token = client.post("/api/auth/login", json={"email": email, "password": "Password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_list_post(client):
    headers = _auth_headers(client)
    resp = client.post("/api/posts", json={"text": "Excited for the fest!", "is_anonymous": False}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["author"]["is_anonymous"] is False

    listing = client.get("/api/posts", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_anonymous_post_hides_real_username(client):
    headers = _auth_headers(client, email="anon@campus.ai", username="realname123")
    resp = client.post("/api/posts", json={"text": "Anonymous confession here", "is_anonymous": True}, headers=headers)
    assert resp.status_code == 201
    author = resp.json()["author"]
    assert author["is_anonymous"] is True
    assert "realname123" not in author["display_name"]
    assert author["display_name"].startswith("Anonymous ")


def test_empty_post_rejected(client):
    headers = _auth_headers(client)
    resp = client.post("/api/posts", json={"text": "   "}, headers=headers)
    assert resp.status_code == 422


def test_unauthenticated_post_rejected(client):
    resp = client.post("/api/posts", json={"text": "hello"})
    assert resp.status_code == 401


def test_comment_on_post(client):
    headers = _auth_headers(client)
    post = client.post("/api/posts", json={"text": "Post for comments"}, headers=headers).json()
    resp = client.post(f"/api/posts/{post['id']}/comments", json={"text": "Nice post!"}, headers=headers)
    assert resp.status_code == 201

    comments = client.get(f"/api/posts/{post['id']}/comments")
    assert len(comments.json()) == 1


def test_reaction_toggle(client):
    headers = _auth_headers(client)
    post = client.post("/api/posts", json={"text": "React to me"}, headers=headers).json()

    r1 = client.post("/api/posts/reactions", json={"target_type": "post", "target_id": post["id"]}, headers=headers)
    assert r1.json()["reacted"] is True

    r2 = client.post("/api/posts/reactions", json={"target_type": "post", "target_id": post["id"]}, headers=headers)
    assert r2.json()["reacted"] is False  # toggled off


def test_poll_vote_and_duplicate_vote_rejected(client):
    headers = _auth_headers(client)
    post = client.post("/api/posts", json={
        "text": "Vote please", "is_anonymous": True,
        "poll": {"question": "Best food?", "options": ["Canteen", "Outside"]},
    }, headers=headers).json()

    option_id = post["poll"]["options"][0]["id"]
    vote1 = client.post(f"/api/posts/polls/{option_id}/vote", headers=headers)
    assert vote1.status_code == 201

    vote2 = client.post(f"/api/posts/polls/{option_id}/vote", headers=headers)
    assert vote2.status_code == 400


def test_delete_post_by_non_author_forbidden(client):
    headers_a = _auth_headers(client, email="a@campus.ai", username="usera")
    headers_b = _auth_headers(client, email="b@campus.ai", username="userb")
    post = client.post("/api/posts", json={"text": "mine"}, headers=headers_a).json()

    resp = client.delete(f"/api/posts/{post['id']}", headers=headers_b)
    assert resp.status_code == 403


def test_xss_input_is_escaped(client):
    headers = _auth_headers(client)
    malicious = "<script>alert('xss')</script>"
    resp = client.post("/api/posts", json={"text": malicious}, headers=headers)
    assert resp.status_code == 201
    stored_text = resp.json()["text"]
    assert "<script>" not in stored_text
    assert "&lt;script&gt;" in stored_text
