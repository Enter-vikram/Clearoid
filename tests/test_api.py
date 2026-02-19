from uuid import uuid4

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.main import app
from database.connection import SessionLocal
from database.models import Title
from backend.routes.auth_routes import User


@pytest.fixture()
def client(monkeypatch):
    def fake_embedding(text: str):
        seed = abs(hash(text)) % (2 ** 32)
        rng = np.random.default_rng(seed)
        return rng.random(8, dtype=np.float32).tolist()

    monkeypatch.setattr("backend.services.title_service.get_embedding", fake_embedding)
    monkeypatch.setattr("backend.routes.title_routes.get_embedding", fake_embedding)
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_test_rows():
    db = SessionLocal()
    try:
        yield
    finally:
        db.execute(delete(Title).where(Title.title.like("TEST_CASE_%")))
        db.execute(delete(User).where(User.email.like("test_case_%")))
        db.commit()
        db.close()


def test_submit_and_read_titles(client):
    payload = {"title": "TEST_CASE_Project Alpha"}
    submit = client.post("/api/submit", json=payload)
    assert submit.status_code == 200
    body = submit.json()
    assert body["title"] == payload["title"]
    assert "id" in body

    titles = client.get("/api/titles?page=1&limit=10&search=TEST_CASE_Project")
    assert titles.status_code == 200
    titles_body = titles.json()
    assert titles_body["total"] >= 1
    assert any(row["title"] == payload["title"] for row in titles_body["data"])


def test_duplicate_scan(client):
    value = "TEST_CASE_Duplicate Name 100"
    first = client.post("/api/submit", json={"title": value})
    assert first.status_code == 200

    check = client.post("/api/check-duplicate", json={"title": value})
    assert check.status_code == 200
    check_body = check.json()
    assert check_body["duplicate"] is True
    assert check_body["match_id"] is not None
    assert 0 <= check_body["score"] <= 1


def test_signup_and_signin(client):
    email = f"test_case_{uuid4().hex[:8]}@example.com"
    password = "testpass123"

    signup = client.post(
        "/auth/signup",
        json={"email": email, "password": password, "name": "Case User"},
    )
    assert signup.status_code == 200
    assert signup.json()["success"] is True

    signin = client.post(
        "/auth/signin",
        json={"email": email, "password": password},
    )
    assert signin.status_code == 200
    assert signin.json()["success"] is True


def test_update_delete_and_export(client):
    created = client.post("/api/submit", json={"title": "TEST_CASE_Edit Me"})
    assert created.status_code == 200
    row_id = created.json()["id"]

    updated = client.put(f"/api/titles/{row_id}", json={"title": "TEST_CASE_Edited Value"})
    assert updated.status_code == 200
    assert updated.json()["title"] == "TEST_CASE_Edited Value"

    exported = client.get("/api/export/excel?type=selected&ids=%s" % row_id)
    assert exported.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in exported.headers.get("content-type", "")

    deleted = client.delete(f"/api/titles/{row_id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] == 1
