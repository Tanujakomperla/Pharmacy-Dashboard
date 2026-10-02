import os
import sqlite3
import pandas as pd


# ============================================================
# DATABASE LOCATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DB_PATH = os.path.join(
    BASE_DIR,
    "data",
    "students.db"
)


# ============================================================
# TABLE SCHEMA
# ============================================================

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT UNIQUE NOT NULL,
    student_name TEXT NOT NULL,
    gender TEXT NOT NULL,
    age INTEGER NOT NULL,
    year TEXT NOT NULL,
    semester INTEGER NOT NULL,
    course TEXT NOT NULL,
    attendance REAL NOT NULL,
    cgpa REAL NOT NULL,
    medicinal_chemistry_ii INTEGER NOT NULL,
    industrial_pharmacy_i INTEGER NOT NULL,
    pharmacology_ii INTEGER NOT NULL,
    pharmacognosy_phytochemistry_ii INTEGER NOT NULL,
    pharmaceutical_jurisprudence INTEGER NOT NULL,
    total_marks INTEGER NOT NULL,
    percentage REAL NOT NULL,
    gpat_mock_score INTEGER NOT NULL,
    internship_status TEXT NOT NULL,
    project_status TEXT NOT NULL,
    backlogs INTEGER NOT NULL,
    placement_status TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


# Maps database column names -> the display names the rest of the
# app (statistics.py, correlation.py, templates) already expects.
COLUMN_MAP = {
    "student_id": "Student ID",
    "student_name": "Student Name",
    "gender": "Gender",
    "age": "Age",
    "year": "Year",
    "semester": "Semester",
    "course": "Course",
    "attendance": "Attendance %",
    "cgpa": "CGPA",
    "medicinal_chemistry_ii": "Medicinal Chemistry - II",
    "industrial_pharmacy_i": "Industrial Pharmacy - I",
    "pharmacology_ii": "Pharmacology - II",
    "pharmacognosy_phytochemistry_ii": "Pharmacognosy and Phytochemistry - II",
    "pharmaceutical_jurisprudence": "Pharmaceutical Jurisprudence",
    "total_marks": "Total Marks",
    "percentage": "Percentage",
    "gpat_mock_score": "GPAT Mock Score",
    "internship_status": "Internship Status",
    "project_status": "Project Status",
    "backlogs": "Backlogs",
    "placement_status": "Placement Status"
}


# ============================================================
# CONNECTION / INITIALISATION
# ============================================================

def get_connection():

    os.makedirs(
        os.path.dirname(DB_PATH),
        exist_ok=True
    )

    conn = sqlite3.connect(DB_PATH)

    conn.execute(SCHEMA)

    return conn


def init_db():
    """Create the students table if it does not already exist."""

    conn = get_connection()

    conn.commit()

    conn.close()


# ============================================================
# NEXT STUDENT ID (P001, P002, ...)
# ============================================================

def get_next_student_id(conn):

    cursor = conn.execute(
        "SELECT student_id FROM students ORDER BY id DESC LIMIT 1"
    )

    row = cursor.fetchone()

    if row is None:
        return "P001"

    last_number = int(row[0][1:])

    return f"P{last_number + 1:03d}"


# ============================================================
# ADD A NEW STUDENT (called from the "Add Student" form)
# ============================================================

def add_student(form):

    conn = get_connection()

    try:

        subject_marks = [
            int(form["medicinal_chemistry_ii"]),
            int(form["industrial_pharmacy_i"]),
            int(form["pharmacology_ii"]),
            int(form["pharmacognosy_phytochemistry_ii"]),
            int(form["pharmaceutical_jurisprudence"])
        ]

        total_marks = sum(subject_marks)

        percentage = round(
            total_marks / (len(subject_marks) * 100) * 100,
            2
        )

        student_id = get_next_student_id(conn)

        conn.execute(
            """
            INSERT INTO students (
                student_id, student_name, gender, age, year, semester, course,
                attendance, cgpa,
                medicinal_chemistry_ii, industrial_pharmacy_i, pharmacology_ii,
                pharmacognosy_phytochemistry_ii, pharmaceutical_jurisprudence,
                total_marks, percentage, gpat_mock_score,
                internship_status, project_status, backlogs, placement_status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                student_id,
                form["student_name"].strip(),
                form["gender"],
                int(form["age"]),
                form.get("year", "3rd Year"),
                int(form.get("semester", 5)),
                form.get("course", "B.Pharm"),
                float(form["attendance"]),
                float(form["cgpa"]),
                *subject_marks,
                total_marks,
                percentage,
                int(form["gpat_mock_score"]),
                form["internship_status"],
                form["project_status"],
                int(form["backlogs"]),
                form["placement_status"]
            )
        )

        conn.commit()

        return student_id

    finally:

        conn.close()


# ============================================================
# LOAD EVERY STUDENT AS A DATAFRAME
# ============================================================

def load_all_as_dataframe():

    conn = get_connection()

    try:

        df = pd.read_sql_query(
            "SELECT * FROM students ORDER BY id ASC",
            conn
        )

    finally:

        conn.close()

    # Always rename, even with 0 rows, so every page sees the same
    # display column names ("Gender", "CGPA", ...) whether the table
    # has data yet or not.
    df = df.drop(
        columns=["id", "created_at"],
        errors="ignore"
    )

    df = df.rename(columns=COLUMN_MAP)

    return df


# ============================================================
# TOTAL STUDENT COUNT (cheap check, no need to load everything)
# ============================================================

def get_student_count():

    conn = get_connection()

    try:

        cursor = conn.execute(
            "SELECT COUNT(*) FROM students"
        )

        return int(cursor.fetchone()[0])

    finally:

        conn.close()
