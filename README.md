# Attendance Manager

A small local-use attendance web application built with Python 3, Flask, SQLite, HTML, Jinja, and CSS.

## Features

- Add and delete student records with unique roll numbers and optional class/group information.
- Mark daily attendance as Present, Absent, or Late.
- View the current-day roster and attendance dashboard.
- Review per-student attendance counts for a selected date range.

## Run locally

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in a browser. The application creates `attendance.db` locally on first run; the database and sample records are not included in this repository.

## Limitations

This coursework-scale starter app has no user accounts or access control. Before any non-local deployment, replace the placeholder Flask secret key and disable debug mode. No automated test suite or test results are included.
