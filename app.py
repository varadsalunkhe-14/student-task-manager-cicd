"""
Personal Task Manager - Flask Backend
--------------------------------------
A complete CRUD application for managing tasks with due dates,
priority levels, and categories/tags. Uses SQLite as the database.

Run with: python app.py
Then open: http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
DB_NAME = os.path.join(os.path.dirname(__file__), "tasks.db")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db_connection():
    """Create a database connection with row access by column name."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the tasks table if it doesn't already exist."""
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'General',
            priority TEXT DEFAULT 'Medium',
            due_date TEXT,
            is_completed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Routes - Web pages (server-rendered)
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Main page: show all tasks, with optional filtering."""
    status_filter = request.args.get("status", "all")     # all | pending | completed
    category_filter = request.args.get("category", "all")

    conn = get_db_connection()

    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if status_filter == "pending":
        query += " AND is_completed = 0"
    elif status_filter == "completed":
        query += " AND is_completed = 1"

    if category_filter != "all":
        query += " AND category = ?"
        params.append(category_filter)

    query += " ORDER BY is_completed ASC, due_date ASC"
    tasks = conn.execute(query, params).fetchall()

    categories = conn.execute(
        "SELECT DISTINCT category FROM tasks ORDER BY category"
    ).fetchall()

    conn.close()
    return render_template(
        "index.html",
        tasks=tasks,
        categories=categories,
        status_filter=status_filter,
        category_filter=category_filter,
    )


@app.route("/add", methods=["POST"])
def add_task():
    """Add a new task."""
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "General").strip() or "General"
    priority = request.form.get("priority", "Medium")
    due_date = request.form.get("due_date", "")

    if not title:
        return redirect(url_for("index"))

    conn = get_db_connection()
    conn.execute(
        """INSERT INTO tasks (title, description, category, priority, due_date, is_completed, created_at)
           VALUES (?, ?, ?, ?, ?, 0, ?)""",
        (title, description, category, priority, due_date, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    """Edit an existing task."""
    conn = get_db_connection()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "General").strip() or "General"
        priority = request.form.get("priority", "Medium")
        due_date = request.form.get("due_date", "")

        conn.execute(
            """UPDATE tasks SET title=?, description=?, category=?, priority=?, due_date=?
               WHERE id=?""",
            (title, description, category, priority, due_date, task_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if task is None:
        return redirect(url_for("index"))
    return render_template("edit.html", task=task)


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    """Delete a task."""
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    """Mark a task complete / incomplete (AJAX-friendly, returns JSON)."""
    conn = get_db_connection()
    task = conn.execute("SELECT is_completed FROM tasks WHERE id = ?", (task_id,)).fetchone()

    if task is None:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    new_status = 0 if task["is_completed"] else 1
    conn.execute("UPDATE tasks SET is_completed = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "is_completed": new_status})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
