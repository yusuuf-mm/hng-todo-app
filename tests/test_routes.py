"""Route tests: HTTP add/toggle/edit/delete/filter/validation."""

import pytest

import db
from app import app as flask_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Test client with isolated temp DB and CSRF off (form token not needed)."""
    monkeypatch.setenv("TODO_DB_PATH", str(tmp_path / "routes.db"))
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    db.init_db()
    with flask_app.test_client() as client:
        yield client


def test_index_empty(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"No tasks yet" in res.data


def test_add_and_filter(client):
    res = client.post("/add", data={"title": "Write tests"}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Write tests" in res.data

    assert b"Write tests" in client.get("/?filter=all").data
    assert b"Write tests" in client.get("/?filter=active").data
    # Not completed yet, so the completed tab shows its own empty state.
    completed = client.get("/?filter=completed")
    assert b"Write tests" not in completed.data
    assert b"No finished tasks yet" in completed.data


def test_add_rejects_empty_and_too_long(client):
    empty = client.post("/add", data={"title": "   "}, follow_redirects=False)
    assert empty.status_code == 400

    long_title = "x" * 201
    too_long = client.post("/add", data={"title": long_title})
    assert too_long.status_code == 400
    assert b"under 200 characters" in too_long.data


def test_toggle_edit_delete_flow(client):
    client.post("/add", data={"title": "Flow task"}, follow_redirects=True)

    # Toggle to done.
    client.post("/toggle/1", follow_redirects=True)
    assert b"Flow task" in client.get("/?filter=completed").data

    # Edit page loads, then saves the new title.
    assert client.get("/edit/1").status_code == 200
    client.post("/edit/1", data={"title": "Renamed"}, follow_redirects=True)
    assert b"Renamed" in client.get("/").data

    # Edit rejects empty title.
    bad = client.post("/edit/1", data={"title": ""})
    assert bad.status_code == 400

    # Delete removes it.
    client.post("/delete/1", follow_redirects=True)
    assert b"Renamed" not in client.get("/").data


def test_edit_missing_task_redirects(client):
    res = client.get("/edit/999", follow_redirects=True)
    assert b"no longer exists" in res.data


def test_clear_completed(client):
    client.post("/add", data={"title": "Keep"}, follow_redirects=True)
    client.post("/add", data={"title": "Drop"}, follow_redirects=True)
    client.post("/toggle/2", follow_redirects=True)
    client.post("/clear-completed", follow_redirects=True)
    body = client.get("/").data
    assert b"Keep" in body
    assert b"Drop" not in body
