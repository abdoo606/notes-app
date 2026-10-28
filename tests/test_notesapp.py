from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from notesapp.app import create_app


@pytest.fixture()
def client():
    with TestClient(create_app()) as c:
        yield c


def test_index_is_empty_initially(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Nothing yet" in response.text


def test_add_note_renders_it(client):
    response = client.post("/notes", data={"title": "Buy milk"})
    assert response.status_code == 200
    assert "Buy milk" in response.text
    assert "1 remaining" in response.text


def test_blank_title_rejected(client):
    assert client.post("/notes", data={"title": "   "}).status_code == 422


def test_toggle_marks_done(client):
    client.post("/notes", data={"title": "Task"})
    response = client.post("/notes/1/toggle")
    assert "0 remaining" in response.text
    assert "✓" in response.text


def test_toggle_twice_restores(client):
    client.post("/notes", data={"title": "Task"})
    client.post("/notes/1/toggle")
    response = client.post("/notes/1/toggle")
    assert "1 remaining" in response.text


def test_delete_note(client):
    client.post("/notes", data={"title": "Temp"})
    response = client.request("DELETE", "/notes/1")
    assert response.status_code == 200
    assert "Temp" not in response.text


def test_missing_note_returns_404(client):
    assert client.request("DELETE", "/notes/99").status_code == 404
    assert client.post("/notes/99/toggle").status_code == 404


def test_html_is_escaped(client):
    response = client.post("/notes", data={"title": "<script>alert(1)</script>"})
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;" in response.text


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
