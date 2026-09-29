"""Flask to-do app. Thin routes: parse form, call db.py, flash + redirect."""

import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

import db
from forms import AddTaskForm, EditTaskForm

# Load .env locally (SECRET_KEY, TODO_DB_PATH). Ignored on Vercel.
load_dotenv()

app = Flask(__name__)
# Flask-WTF CSRF needs a real secret in production.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")

# Create the SQLite table on startup (also covers Vercel cold starts).
db.init_db()


@app.route("/", methods=["GET"])
def index():
    """Show the task list for ?filter=all|active|completed."""
    current = request.args.get("filter", "all")
    if current not in ("all", "active", "completed"):
        current = "all"
    form = AddTaskForm()
    tasks = db.get_tasks(current)
    counts = db.get_counts()
    return render_template("index.html", form=form, tasks=tasks, current=current, counts=counts)


@app.route("/add", methods=["POST"])
def add():
    """Add a task. Invalid input re-renders the list with an inline error."""
    form = AddTaskForm()
    if form.validate_on_submit():
        title = form.title.data.strip()
        if not title:
            flash("Type a task first.", "error")
        else:
            db.add_task(title[:200])
            flash("Task added.", "ok")
        return redirect(url_for("index"))
    # Validation failed: show the list again with the error under the input.
    current = request.args.get("filter", "all")
    tasks = db.get_tasks(current)
    counts = db.get_counts()
    return render_template(
        "index.html", form=form, tasks=tasks, current=current, counts=counts
    ), 400


@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle(task_id: int):
    """Flip a task between active and completed, keep the current filter."""
    db.toggle_task(task_id)
    return redirect(url_for("index", filter=request.args.get("filter", "all")))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id: int):
    """Delete one task."""
    db.delete_task(task_id)
    flash("Task deleted.", "ok")
    return redirect(url_for("index", filter=request.args.get("filter", "all")))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id: int):
    """Show the edit form (GET) or save the new title (POST)."""
    task = db.get_task(task_id)
    if task is None:
        flash("That task no longer exists.", "error")
        return redirect(url_for("index"))
    form = EditTaskForm()
    if request.method == "GET":
        # Pre-fill the form with the current title.
        form.title.data = task["title"]
        return render_template("edit.html", form=form, task=task)
    if form.validate_on_submit():
        title = form.title.data.strip()
        if not title:
            flash("Title cannot be empty.", "error")
            return render_template("edit.html", form=form, task=task), 400
        db.update_title(task_id, title[:200])
        flash("Task updated.", "ok")
        return redirect(url_for("index"))
    return render_template("edit.html", form=form, task=task), 400


@app.route("/clear-completed", methods=["POST"])
def clear_completed():
    """Delete all completed tasks."""
    db.clear_completed()
    flash("Completed tasks cleared.", "ok")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
