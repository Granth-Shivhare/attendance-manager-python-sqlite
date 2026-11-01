from datetime import date
from pathlib import Path
import sqlite3

from flask import Flask, flash, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "attendance.db"
app = Flask(__name__)
app.secret_key = "replace-this-with-a-random-secret-key"


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_number TEXT NOT NULL UNIQUE,
                class_name TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                attendance_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late')),
                UNIQUE(student_id, attendance_date)
            );
        """)


@app.route("/")
def index():
    today = date.today().isoformat()
    with get_db() as db:
        student_count = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        rows = db.execute("""
            SELECT s.name, s.roll_number, s.class_name, a.status
            FROM students s LEFT JOIN attendance a
              ON a.student_id = s.id AND a.attendance_date = ?
            ORDER BY s.name
        """, (today,)).fetchall()
    return render_template("index.html", page="dashboard", today=today, student_count=student_count, rows=rows)


@app.route("/students", methods=["GET", "POST"])
def students():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll = request.form.get("roll_number", "").strip()
        class_name = request.form.get("class_name", "").strip()
        if not name or not roll:
            flash("Name and roll number are required.", "error")
        else:
            try:
                with get_db() as db:
                    db.execute("INSERT INTO students(name, roll_number, class_name) VALUES (?, ?, ?)",
                               (name, roll, class_name))
                flash("Student added.", "success")
                return redirect(url_for("students"))
            except sqlite3.IntegrityError:
                flash("That roll number is already in use.", "error")
    with get_db() as db:
        records = db.execute("SELECT * FROM students ORDER BY name").fetchall()
    return render_template("index.html", page="students", students=records)


@app.post("/students/<int:student_id>/delete")
def delete_student(student_id):
    with get_db() as db:
        db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    flash("Student deleted.", "success")
    return redirect(url_for("students"))


@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    selected_date = request.values.get("attendance_date", date.today().isoformat())
    if request.method == "POST":
        with get_db() as db:
            students_list = db.execute("SELECT id FROM students").fetchall()
            for student in students_list:
                status = request.form.get(f"status_{student['id']}", "Absent")
                if status not in ("Present", "Absent", "Late"):
                    status = "Absent"
                db.execute("""INSERT INTO attendance(student_id, attendance_date, status)
                              VALUES (?, ?, ?)
                              ON CONFLICT(student_id, attendance_date)
                              DO UPDATE SET status = excluded.status""",
                           (student["id"], selected_date, status))
        flash(f"Attendance saved for {selected_date}.", "success")
        return redirect(url_for("attendance", attendance_date=selected_date))
    with get_db() as db:
        records = db.execute("""
            SELECT s.id, s.name, s.roll_number, s.class_name, a.status
            FROM students s LEFT JOIN attendance a
              ON a.student_id = s.id AND a.attendance_date = ?
            ORDER BY s.name
        """, (selected_date,)).fetchall()
    return render_template("index.html", page="attendance", students=records, selected_date=selected_date)


@app.route("/report")
def report():
    start = request.args.get("start", date.today().replace(day=1).isoformat())
    end = request.args.get("end", date.today().isoformat())
    with get_db() as db:
        records = db.execute("""
            SELECT s.name, s.roll_number, s.class_name,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present,
                   SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absent,
                   SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) AS late,
                   COUNT(a.id) AS marked
            FROM students s LEFT JOIN attendance a
              ON a.student_id = s.id AND a.attendance_date BETWEEN ? AND ?
            GROUP BY s.id ORDER BY s.name
        """, (start, end)).fetchall()
    return render_template("index.html", page="report", students=records, start=start, end=end)


init_db()

if __name__ == "__main__":
    app.run(debug=True)
