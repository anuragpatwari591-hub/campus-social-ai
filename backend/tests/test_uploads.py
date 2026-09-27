import io

from tests.conftest import register_user


def _auth_headers(client):
    register_user(client, email="up@campus.ai", username="upuser")
    token = client.post("/api/auth/login", json={"email": "up@campus.ai", "password": "Password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_valid_image(client):
    headers = _auth_headers(client)
    fake_image = io.BytesIO(b"\xff\xd8\xff\xe0fakejpegcontent")
    resp = client.post("/api/uploads/image", files={"file": ("test.jpg", fake_image, "image/jpeg")}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["url"].startswith("/test_uploads")


def test_upload_rejects_disallowed_type(client):
    headers = _auth_headers(client)
    fake_exe = io.BytesIO(b"MZfakeexecutable")
    resp = client.post("/api/uploads/image", files={"file": ("virus.exe", fake_exe, "application/x-msdownload")}, headers=headers)
    assert resp.status_code == 400


def test_upload_rejects_empty_file(client):
    headers = _auth_headers(client)
    empty = io.BytesIO(b"")
    resp = client.post("/api/uploads/image", files={"file": ("empty.png", empty, "image/png")}, headers=headers)
    assert resp.status_code == 400


def test_upload_requires_authentication(client):
    fake_image = io.BytesIO(b"fake")
    resp = client.post("/api/uploads/image", files={"file": ("test.png", fake_image, "image/png")})
    assert resp.status_code == 401
