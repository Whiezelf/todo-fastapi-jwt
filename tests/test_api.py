import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

PASSWORD = "password-valida-123"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def new_user(client):
    """Registra un utente nuovo e restituisce (headers, email)."""
    email = f"{uuid.uuid4().hex[:10]}@example.com"
    r = client.post("/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201
    r = client.post("/login", data={"username": email, "password": PASSWORD})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}, email


def test_register_does_not_leak_password(client):
    r = client.post("/register", json={"email": "a1@example.com", "password": PASSWORD})
    assert r.status_code == 201
    assert "password" not in r.text and "hashed" not in r.text


def test_register_duplicate_email(client):
    client.post("/register", json={"email": "dup@example.com", "password": PASSWORD})
    r = client.post("/register", json={"email": "DUP@example.com", "password": PASSWORD})
    assert r.status_code == 400


def test_register_rejects_short_password(client):
    r = client.post("/register", json={"email": "short@example.com", "password": "123"})
    assert r.status_code == 422


def test_login_wrong_password(client):
    _, email = new_user(client)
    r = client.post("/login", data={"username": email, "password": "sbagliata-123"})
    assert r.status_code == 401


def test_todos_require_token(client):
    assert client.get("/todos/").status_code == 401
    assert client.get("/todos/", headers={"Authorization": "Bearer falso"}).status_code == 401


def test_todo_crud(client):
    h, _ = new_user(client)
    r = client.post("/todos/", json={"title": "Studiare", "description": "FastAPI"}, headers=h)
    assert r.status_code == 201
    todo = r.json()
    assert todo["completed"] is False

    r = client.put(f"/todos/{todo['id']}", json={"completed": True}, headers=h)
    assert r.status_code == 200 and r.json()["completed"] is True
    assert r.json()["title"] == "Studiare"

    assert len(client.get("/todos/", headers=h).json()) == 1
    assert client.delete(f"/todos/{todo['id']}", headers=h).status_code == 200
    assert client.get(f"/todos/{todo['id']}", headers=h).status_code == 404


def test_empty_title_rejected(client):
    h, _ = new_user(client)
    assert client.post("/todos/", json={"title": "   "}, headers=h).status_code == 422


def test_users_cannot_access_each_others_todos(client):
    h_a, _ = new_user(client)
    h_b, _ = new_user(client)
    todo_id = client.post("/todos/", json={"title": "Privato"}, headers=h_a).json()["id"]

    assert client.get(f"/todos/{todo_id}", headers=h_b).status_code == 404
    assert client.put(f"/todos/{todo_id}", json={"title": "Hack"}, headers=h_b).status_code == 404
    assert client.delete(f"/todos/{todo_id}", headers=h_b).status_code == 404
    assert client.get("/todos/", headers=h_b).json() == []
    assert client.get(f"/todos/{todo_id}", headers=h_a).status_code == 200


def test_delete_account_wrong_password(client):
    h, email = new_user(client)
    r = client.request("DELETE", "/me", json={"password": "sbagliata-123"}, headers=h)
    assert r.status_code == 401

    # l'utente deve esistere ancora: il login con la password giusta funziona
    r = client.post("/login", data={"username": email, "password": PASSWORD})
    assert r.status_code == 200


def test_delete_account_success(client):
    h, email = new_user(client)
    client.post("/todos/", json={"title": "Da cancellare"}, headers=h)

    r = client.request("DELETE", "/me", json={"password": PASSWORD}, headers=h)
    assert r.status_code == 204

    # login con le stesse credenziali deve fallire: l'account non esiste più
    r = client.post("/login", data={"username": email, "password": PASSWORD})
    assert r.status_code == 401

    # il token vecchio non deve funzionare più, perché l'utente non c'è
    assert client.get("/todos/", headers=h).status_code == 401