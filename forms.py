"""Flask-WTF forms. All validation lives here; routes just call db.py."""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class AddTaskForm(FlaskForm):
    """Form on the index page for creating a task."""

    title = StringField(
        "New task",
        validators=[
            DataRequired(message="Type a task first."),
            Length(max=200, message="Keep it under 200 characters."),
        ],
    )
    submit = SubmitField("Add")


class EditTaskForm(FlaskForm):
    """Form on the edit page for renaming a task."""

    title = StringField(
        "Task title",
        validators=[
            DataRequired(message="Title cannot be empty."),
            Length(max=200, message="Keep it under 200 characters."),
        ],
    )
    submit = SubmitField("Save")
