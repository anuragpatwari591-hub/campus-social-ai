from tests.conftest import register_user


def _login(client, email, username):
    register_user(client, email=email, username=username)
    token = client.post("/api/auth/login", json={"email": email, "password": "Password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _make_admin(client, username):
    from tests.conftest import TestSessionLocal
    from app.models.user import User, UserRole
    db = TestSessionLocal()
    user = db.query(User).filter_by(username=username).first()
    user.role = UserRole.ADMIN
    db.commit()
    db.close()


def _make_moderator(client, username):
    from tests.conftest import TestSessionLocal
    from app.models.user import User, UserRole
    db = TestSessionLocal()
    user = db.query(User).filter_by(username=username).first()
    user.role = UserRole.MODERATOR
    db.commit()
    db.close()


def test_student_cannot_access_admin_analytics(client):
    headers = _login(client, "s1@campus.ai", "student1")
    resp = client.get("/api/admin/analytics", headers=headers)
    assert resp.status_code == 403


def test_admin_can_access_analytics_with_real_counts(client):
    headers = _login(client, "adm@campus.ai", "adminuser")
    _make_admin(client, "adminuser")
    # re-login to be safe (role is read fresh from DB each request, no re-login needed)
    resp = client.get("/api/admin/analytics", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["registered_users"] >= 1
    assert "pending_reports" in body


def test_report_creation_and_moderator_review(client):
    reporter_headers = _login(client, "rep@campus.ai", "reporter1")
    post = client.post("/api/posts", json={"text": "questionable content"}, headers=reporter_headers).json()

    report_resp = client.post("/api/moderation/reports", json={
        "target_type": "post", "target_id": post["id"], "reason": "spam",
    }, headers=reporter_headers)
    assert report_resp.status_code == 201

    mod_headers = _login(client, "modtest@campus.ai", "modtest1")
    _make_moderator(client, "modtest1")

    forbidden = client.get("/api/moderation/reports", headers=reporter_headers)
    assert forbidden.status_code == 403

    allowed = client.get("/api/moderation/reports", headers=mod_headers)
    assert allowed.status_code == 200
    assert len(allowed.json()) == 1


def test_moderator_can_remove_content(client):
    author_headers = _login(client, "author1@campus.ai", "author1")
    post = client.post("/api/posts", json={"text": "to be removed"}, headers=author_headers).json()

    mod_headers = _login(client, "modtest2@campus.ai", "modtest2")
    _make_moderator(client, "modtest2")

    resp = client.post("/api/moderation/actions", json={
        "action": "remove_content", "target_type": "post", "target_id": post["id"],
    }, headers=mod_headers)
    assert resp.status_code == 201

    get_resp = client.get(f"/api/posts/{post['id']}", headers=author_headers)
    assert get_resp.status_code == 404


def test_unauthorized_admin_role_change_rejected(client):
    headers = _login(client, "u1@campus.ai", "regularuser")
    resp = client.post("/api/admin/users/1/role", params={"role": "admin"}, headers=headers)
    assert resp.status_code == 403
