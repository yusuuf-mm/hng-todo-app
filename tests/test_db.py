"""DB tests: CRUD, filter, counts. Each test gets a fresh temp SQLite file."""

import os

import db


def use_tmp_db(tmp_path, monkeypatch):
    """Point db.py at an isolated temp file and create the table."""
    path = str(tmp_path / "test.db")
    monkeypatch.setenv("TODO_DB_PATH", path)
    assert db.get_db_path() == path
    db.init_db()
    return path


def test_add_and_get(tmp_path, monkeypatch):
    use_tmp_db(tmp_path, monkeypatch)
    task_id = db.add_task("Buy milk")
    task = db.get_task(task_id)
    assert task["title"] == "Buy milk"
    assert task["done"] == 0


def test_filter_active_completed(tmp_path, monkeypatch):
    use_tmp_db(tmp_path, monkeypatch)
    a = db.add_task("Active one")
    b = db.add_task("Done one")
    db.toggle_task(b)  # mark done
    assert [t["id"] for t in db.get_tasks("active")] == [a]
    assert [t["id"] for t in db.get_tasks("completed")] == [b]
    assert len(db.get_tasks("all")) == 2
    # Unknown filter falls back to all.
    assert len(db.get_tasks("bogus")) == 2


def test_toggle_update_delete_counts(tmp_path, monkeypatch):
    use_tmp_db(tmp_path, monkeypatch)
    task_id = db.add_task("Old title")
    db.toggle_task(task_id)
    assert db.get_task(task_id)["done"] == 1
    db.toggle_task(task_id)
    assert db.get_task(task_id)["done"] == 0

    db.update_title(task_id, "New title")
    assert db.get_task(task_id)["title"] == "New title"

    counts = db.get_counts()
    assert counts == {"total": 1, "active": 1, "completed": 0}

    db.delete_task(task_id)
    assert db.get_task(task_id) is None
    assert os.path.exists(db.get_db_path())  # file itself stays


def test_clear_completed(tmp_path, monkeypatch):
    use_tmp_db(tmp_path, monkeypatch)
    db.add_task("Keep me")
    done_id = db.add_task("Remove me")
    db.toggle_task(done_id)
    db.clear_completed()
    remaining = db.get_tasks("all")
    assert [t["title"] for t in remaining] == ["Keep me"]
