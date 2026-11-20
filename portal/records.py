"""Student marks: validation + database access through the Django ORM."""
import math

import pandas as pd
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count

from config.routers import student_alias
from .models import StudentRecord

GENDERS = ("Female", "Male", "Other")
PROGRESS = ("Not Started", "Ongoing", "Completed")
PLACEMENT = ("Not Yet", "Preparing", "Placed")

SUBJECT_FIELDS = [
    "medicinal_chemistry_ii",
    "industrial_pharmacy_i",
    "pharmacology_ii",
    "pharmacognosy_phytochemistry_ii",
    "pharmaceutical_jurisprudence",
]

# ------------------------------------------------------------
# schema
# ------------------------------------------------------------

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
    "placement_status": "Placement Status",
}


def clean_student_form(form, student_name=None):
    """Check every field and return a clean dict. Raises ValueError with
    a friendly message when something is missing or out of range."""

    def whole(key, label, low, high):
        raw = str(form.get(key, "")).strip()
        if raw == "":
            raise ValueError("%s is required." % label)
        try:
            value = int(raw)
        except ValueError:
            raise ValueError("%s must be a whole number." % label)
        if not low <= value <= high:
            raise ValueError("%s must be between %s and %s." % (label, low, high))
        return value

    def decimal(key, label, low, high):
        raw = str(form.get(key, "")).strip()
        if raw == "":
            raise ValueError("%s is required." % label)
        try:
            value = float(raw)
        except ValueError:
            raise ValueError("%s must be a number." % label)
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError("%s must be between %s and %s." % (label, low, high))
        return value

    def choice(key, label, allowed):
        value = str(form.get(key, "")).strip()
        if value not in allowed:
            raise ValueError("Please choose a valid option for %s." % label)
        return value

    name = (student_name if student_name is not None
            else form.get("student_name", "")).strip()

    if not name or len(name) > 80:
        raise ValueError("Student name is required (up to 80 characters).")

    marks = [
        whole(field, label, 0, 100)
        for field, label in zip(SUBJECT_FIELDS, [
            "Medicinal Chemistry - II", "Industrial Pharmacy - I",
            "Pharmacology - II", "Pharmacognosy and Phytochemistry - II",
            "Pharmaceutical Jurisprudence"])
    ]

    total = sum(marks)

    cleaned = {
        "student_name": name,
        "gender": choice("gender", "Gender", GENDERS),
        "age": whole("age", "Age", 16, 60),
        "year": "3rd Year",
        "semester": 5,
        "course": "B.Pharm",
        "attendance": decimal("attendance", "Attendance %", 0, 100),
        "cgpa": decimal("cgpa", "CGPA", 0, 10),
        "total_marks": total,
        "percentage": round(total / (len(marks) * 100) * 100, 2),
        "gpat_mock_score": whole("gpat_mock_score", "GPAT mock score", 0, 200),
        "internship_status": choice("internship_status", "Internship status", PROGRESS),
        "project_status": choice("project_status", "Project status", PROGRESS),
        "backlogs": whole("backlogs", "Backlogs", 0, 50),
        "placement_status": choice("placement_status", "Placement status", PLACEMENT),
    }

    for field, value in zip(SUBJECT_FIELDS, marks):
        cleaned[field] = value

    return cleaned




def _db():
    return student_alias()


def _next_student_id():
    best = 0
    for sid in StudentRecord.objects.using(_db()).values_list("student_id", flat=True):
        try:
            best = max(best, int(sid[1:]))
        except ValueError:
            pass
    return "P%03d" % (best + 1)



def add_student(form, user_id=None, source="admin", student_name=None):
    """Create a record (used by the admin 'Add Student' page)."""
    cleaned = clean_student_form(form, student_name=student_name)
    for _ in range(6):
        try:
            with transaction.atomic(using=_db()):
                record = StudentRecord.objects.using(_db()).create(
                    student_id=_next_student_id(), user_id=user_id, source=source, **cleaned
                )
            return record.student_id
        except IntegrityError:
            continue  # two people saved at once - try the next free ID
    raise ValueError("Could not save, please try again.")


def save_student_submission(user, form):
    """A student saves (or edits) THEIR OWN marks. One row per login account."""
    cleaned = clean_student_form(form, student_name=user["name"])
    qs = StudentRecord.objects.using(_db())
    existing = qs.filter(user_id=user["id"]).first()
    if existing:
        for key, value in cleaned.items():
            setattr(existing, key, value)
        existing.save(using=_db())
        return existing.student_id
    return add_student(form, user_id=user["id"], source="student", student_name=user["name"])


def delete_student_record(student_id):
    StudentRecord.objects.using(_db()).filter(student_id=student_id).delete()


def get_submission_for_user(user_id):
    return StudentRecord.objects.using(_db()).filter(user_id=user_id).values().first()


def list_records():
    return list(StudentRecord.objects.using(_db()).order_by("id").values())


def class_averages():
    """Whole-class averages only (never individual rows)."""
    agg = StudentRecord.objects.using(_db()).aggregate(
        n=Count("id"), percentage=Avg("percentage"), cgpa=Avg("cgpa"),
        attendance=Avg("attendance"), **{f: Avg(f) for f in SUBJECT_FIELDS}
    )
    result = {"n": int(agg.pop("n"))}
    for key, value in agg.items():
        result[key] = round(float(value), 1) if value is not None else 0.0
    return result


def load_all_as_dataframe():
    rows = list(StudentRecord.objects.using(_db()).order_by("id").values())
    columns = ["student_id", "student_name", "gender", "age", "year", "semester", "course",
               "attendance", "cgpa", *SUBJECT_FIELDS, "total_marks", "percentage",
               "gpat_mock_score", "internship_status", "project_status", "backlogs",
               "placement_status"]
    df = pd.DataFrame(rows, columns=None if rows else columns)
    df = df[columns]
    return df.rename(columns=COLUMN_MAP)


def get_student_count():
    return StudentRecord.objects.using(_db()).count()
