import csv
import hmac
import io
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render as dj_render
from django.views.decorators.http import require_POST

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

from analysis.statistics import calculate_statistics
from analysis.correlation import calculate_correlations
from . import accounts, events
from .analytics import (
    MIN_STUDENTS_FOR_PREDICTION, SUBJECT_COLUMNS, PREDICTION_FEATURES, PREDICTION_TARGET,
    get_data, safe_mean, dataframe_to_records, get_summary, common_context,
)
from .context import current_user_dict
from .records import (
    SUBJECT_FIELDS, add_student, class_averages, delete_student_record,
    get_submission_for_user, list_records, load_all_as_dataframe,
    save_student_submission,
)

SUBJECT_LABELS = [
    ("medicinal_chemistry_ii", "Medicinal Chemistry - II"),
    ("industrial_pharmacy_i", "Industrial Pharmacy - I"),
    ("pharmacology_ii", "Pharmacology - II"),
    ("pharmacognosy_phytochemistry_ii", "Pharmacognosy and Phytochemistry - II"),
    ("pharmaceutical_jurisprudence", "Pharmaceutical Jurisprudence"),
]

_failed_logins = {}


def render(request, template, status=200, **context):
    """render_template() look-alike: render(request, "x.html", a=1, b=2)"""
    response = dj_render(request, template, context, status=status)
    response["Cache-Control"] = "no-store"
    return response


def render_error(request, code, message):
    return render(request, "error.html", status=code, code=code, message=message)


def csrf_failed(request, reason=""):
    return render_error(
        request, 400,
        "Your session expired. Please go back, refresh the page and try again.",
    )


def page_not_found(request, exception=None):
    return render_error(request, 404, "That page does not exist.")


def healthz(request):
    return HttpResponse("ok")


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "")


def _too_many_attempts(key):
    now = time.time()
    recent = [t for t in _failed_logins.get(key, []) if now - t < 600]
    _failed_logins[key] = recent
    return len(recent) >= 5


# ============================================================
# ADMIN ANALYTICS PAGES (same pages as before)
# ============================================================

def index(request):
    df = get_data()
    return render(request, "index.html", **common_context(df))


def students_information(request):
    df = get_data()
    context = common_context(df)
    records = dataframe_to_records(df)
    return render(
        request, "students_information.html", **context,
        students=records, student_data=records, columns=list(df.columns),
        genders=sorted(df["Gender"].dropna().unique().tolist()),
        internships=sorted(df["Internship Status"].dropna().unique().tolist()),
        projects=sorted(df["Project Status"].dropna().unique().tolist()),
        placements=sorted(df["Placement Status"].dropna().unique().tolist()),
    )


def academic_analysis(request):
    df = get_data()
    context = common_context(df)
    subject_averages = {s: safe_mean(df[s]) for s in SUBJECT_COLUMNS if s in df.columns}
    highest = max(subject_averages, key=subject_averages.get) if subject_averages else None
    lowest = min(subject_averages, key=subject_averages.get) if subject_averages else None
    records = dataframe_to_records(df)
    return render(
        request, "academic_analysis.html", **context,
        subject_columns=SUBJECT_COLUMNS, subject_averages=subject_averages,
        subject_labels=list(subject_averages.keys()),
        subject_values=list(subject_averages.values()),
        highest_subject=highest, lowest_subject=lowest,
        students=records, student_data=records, academic_students=records,
        subjects=SUBJECT_COLUMNS,
        overall_cgpa=context["average_cgpa"],
        overall_percentage=context["average_percentage"],
        columns=list(df.columns),
    )


def statistics(request):
    df = get_data()
    data = calculate_statistics(df)
    return render(request, "statistics.html", statistics_data=data,
                  statistics=data, student_count=len(df))


def correlation(request):
    df = get_data()
    data = calculate_correlations(df)
    ordered = dict(sorted(data.items(), key=lambda item: abs(item[1]), reverse=True))
    labels, values = list(ordered.keys()), list(ordered.values())
    return render(
        request, "correlation.html",
        correlation_data=data, sorted_correlations=ordered,
        correlation_labels=labels, correlation_values=values,
        strongest_feature=labels[0] if ordered else None,
        strongest_value=values[0] if ordered else None,
        target="Percentage", target_variable="Percentage", student_count=len(df),
    )


def prediction(request):

    df = get_data()


    # --------------------------------------------------------
    # NOT ENOUGH DATA YET
    # --------------------------------------------------------
    # The regression model needs a reasonable number of students
    # before a train/test split means anything. Early on (right
    # after launch, or the first day of data entry) we skip
    # training instead of crashing or showing a meaningless model.

    if len(df) < MIN_STUDENTS_FOR_PREDICTION:

        return render(request, 

            "prediction.html",

            insufficient_data=True,

            students_needed=MIN_STUDENTS_FOR_PREDICTION,

            model=None,

            prediction=None,

            prediction_result=None,

            target=PREDICTION_TARGET,

            target_variable=PREDICTION_TARGET,

            features=PREDICTION_FEATURES,

            feature_count=len(PREDICTION_FEATURES),

            student_count=len(df),

            r2_score=None,

            mae=None,

            mse=None,

            rmse=None

        )


    # --------------------------------------------------------
    # PREPARE MODEL DATA
    # --------------------------------------------------------

    model_df = df[
        PREDICTION_FEATURES
        + [PREDICTION_TARGET]
    ].copy()


    # Convert all model columns to numeric

    for column in (
        PREDICTION_FEATURES
        + [PREDICTION_TARGET]
    ):

        model_df[column] = pd.to_numeric(
            model_df[column],
            errors="coerce"
        )


    # Remove missing rows

    model_df = model_df.dropna()


    # --------------------------------------------------------
    # X AND Y
    # --------------------------------------------------------

    X = model_df[
        PREDICTION_FEATURES
    ]

    y = model_df[
        PREDICTION_TARGET
    ]


    # --------------------------------------------------------
    # TRAIN / TEST SPLIT
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42
        )
    )


    # --------------------------------------------------------
    # TRAIN MODEL
    # --------------------------------------------------------

    model = LinearRegression()

    model.fit(
        X_train,
        y_train
    )


    # --------------------------------------------------------
    # TEST PREDICTIONS
    # --------------------------------------------------------

    y_pred = model.predict(
        X_test
    )


    # --------------------------------------------------------
    # MODEL METRICS
    # --------------------------------------------------------

    r2 = round(
        float(
            r2_score(
                y_test,
                y_pred
            )
        ),
        4
    )


    mae = round(
        float(
            mean_absolute_error(
                y_test,
                y_pred
            )
        ),
        4
    )


    mse = round(
        float(
            mean_squared_error(
                y_test,
                y_pred
            )
        ),
        4
    )


    rmse = round(
        float(
            np.sqrt(mse)
        ),
        4
    )


    # --------------------------------------------------------
    # USER PREDICTION
    # --------------------------------------------------------

    prediction_result = None


    if request.method == "POST":

        try:

            attendance = float(
                request.POST.get(
                    "attendance"
                )
            )

            gpat_score = float(
                request.POST.get(
                    "gpat_score"
                )
            )

            backlogs = float(
                request.POST.get(
                    "backlogs"
                )
            )

            age = float(
                request.POST.get(
                    "age"
                )
            )


            # Create input dataframe

            input_data = pd.DataFrame(

                [[
                    attendance,
                    gpat_score,
                    backlogs,
                    age
                ]],

                columns=PREDICTION_FEATURES

            )


            # Predict

            prediction_result = round(

                float(
                    model.predict(
                        input_data
                    )[0]
                ),

                2

            )


        except (
            ValueError,
            TypeError
        ):

            prediction_result = None


    # --------------------------------------------------------
    # SEND TO HTML
    # --------------------------------------------------------

    return render(request, 

        "prediction.html",

        model=model,

        prediction=prediction_result,

        prediction_result=prediction_result,

        target=PREDICTION_TARGET,

        target_variable=PREDICTION_TARGET,

        features=PREDICTION_FEATURES,

        feature_count=len(
            PREDICTION_FEATURES
        ),

        student_count=len(df),

        r2_score=r2,

        mae=mae,

        mse=mse,

        rmse=rmse

    )


# ============================================================
# ADD STUDENT (saves straight to the database, no Excel involved)
# ============================================================

ADD_STUDENT_REQUIRED_FIELDS = [
    "student_name",
    "gender",
    "age",
    "attendance",
    "cgpa",
    "medicinal_chemistry_ii",
    "industrial_pharmacy_i",
    "pharmacology_ii",
    "pharmacognosy_phytochemistry_ii",
    "pharmaceutical_jurisprudence",
    "gpat_mock_score",
    "internship_status",
    "project_status",
    "backlogs",
    "placement_status"
]

ADD_STUDENT_REQUIRED_FIELDS = [
    "student_name", "gender", "age", "attendance", "cgpa",
    *SUBJECT_FIELDS, "gpat_mock_score", "internship_status",
    "project_status", "backlogs", "placement_status",
]


def add_student_page(request):
    if request.method == "POST":
        form = request.POST
        missing = [f for f in ADD_STUDENT_REQUIRED_FIELDS if not form.get(f, "").strip()]
        if missing:
            messages.error(request, "Please fill in every field before submitting.")
            return render(request, "add_student.html", form=form)
        try:
            new_id = add_student(form)
        except ValueError as error:
            messages.error(request, str(error))
            return render(request, "add_student.html", form=form)
        messages.success(
            request,
            f"Saved! {form['student_name']} was added as {new_id}. "
            "The dashboard now includes this record.",
        )
        return redirect("students_information")
    return render(request, "add_student.html", form={})


def api_data(request):
    return JsonResponse(dataframe_to_records(get_data()), safe=False)


def api_summary(request):
    return JsonResponse(get_summary(get_data()), safe=False)


def api_statistics(request):
    return JsonResponse(calculate_statistics(get_data()), safe=False)


def api_correlation(request):
    return JsonResponse(calculate_correlations(get_data()), safe=False)


# ============================================================
# LOGIN / REGISTER / LOGOUT
# ============================================================

def login(request):
    email = ""
    if request.method == "POST":
        email = accounts.clean_email(request.POST.get("email"))
        key = f"{_client_ip(request)}|{email}"
        if _too_many_attempts(key):
            messages.error(request, "Too many failed attempts. Please wait 10 minutes and try again.")
            return render(request, "login.html", status=429, email=email)
        user = accounts.verify_login(email, request.POST.get("password", ""))
        if user is None:
            _failed_logins.setdefault(key, []).append(time.time())
            messages.error(request, "Incorrect email or password.")
            return render(request, "login.html", email=email)
        _failed_logins.pop(key, None)
        auth_login(request, user)
        return redirect("index" if user.is_staff else "student_dashboard")
    return render(request, "login.html", email=email)


def register(request):
    form = request.POST if request.method == "POST" else {}
    needs_code = bool(settings.STUDENT_SIGNUP_CODE)
    if request.method == "POST":
        try:
            if needs_code and not hmac.compare_digest(
                form.get("signup_code", "").strip(), settings.STUDENT_SIGNUP_CODE
            ):
                raise ValueError("Wrong sign-up code. Ask your teacher for the code.")
            if form.get("password", "") != form.get("confirm_password", ""):
                raise ValueError("The two passwords do not match.")
            user = accounts.create_user(
                form.get("name"), form.get("email"), form.get("password", ""), role="student"
            )
        except ValueError as error:
            messages.error(request, str(error))
            return render(request, "register.html", form=form, needs_code=needs_code)
        auth_login(request, user)
        messages.success(request, "Account created. Please fill in your marks form below.")
        return redirect("student_submit")
    return render(request, "register.html", form=form, needs_code=needs_code)


@require_POST
def logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


# ============================================================
# STUDENT PORTAL (a student only ever sees their own data)
# ============================================================

def student_dashboard(request):
    user = current_user_dict(request)
    submission = get_submission_for_user(user["id"])
    averages = None
    if submission:
        stats = class_averages()
        if stats["n"] >= settings.MIN_CLASS_FOR_COMPARISON:
            averages = stats
    subject_rows = []
    if submission:
        for field, label in SUBJECT_LABELS:
            subject_rows.append({
                "label": label, "mark": submission[field],
                "class_avg": averages[field] if averages else None,
            })
    joined_ids = events.user_section_ids(user["id"])
    joined = [s for s in events.list_sections() if s["id"] in joined_ids]
    return render(request, "student_dashboard.html", submission=submission,
                  subject_rows=subject_rows, class_avgs=averages, joined=joined)


def student_submit(request):
    user = current_user_dict(request)
    existing = get_submission_for_user(user["id"])
    if request.method == "POST":
        try:
            save_student_submission(user, request.POST)
        except ValueError as error:
            messages.error(request, str(error))
            return render(request, "student_form.html", form=request.POST, existing=existing)
        messages.success(request, "Your marks were saved. Thank you!")
        return redirect("student_dashboard")
    return render(request, "student_form.html", form=existing or {}, existing=existing)


def student_events(request):
    user = current_user_dict(request)
    return render(request, "student_events.html", sections=events.list_sections(),
                  joined_ids=events.user_section_ids(user["id"]))


@require_POST
def student_join(request, section_id):
    try:
        events.join_section(current_user_dict(request), section_id)
        messages.success(request, "You are registered for this section.")
    except ValueError as error:
        messages.error(request, str(error))
    return redirect("student_events")


@require_POST
def student_leave(request, section_id):
    events.leave_section(current_user_dict(request)["id"], section_id)
    messages.success(request, "You have left this section.")
    return redirect("student_events")


# ============================================================
# ADMIN: SUBMISSIONS TRACKER, EVENTS, EXPORT
# ============================================================

def admin_submissions(request):
    students = accounts.list_students()
    records = list_records()
    by_user = {r["user_id"]: r for r in records if r["user_id"] is not None}
    manual_records = [r for r in records if r["user_id"] is None]
    tracker = [
        {"name": u["first_name"], "email": u["email"],
         "registered": u["date_joined"], "record": by_user.get(u["id"])}
        for u in students
    ]
    submitted = sum(1 for row in tracker if row["record"])
    needs_attention = []
    for r in records:
        reasons = []
        if r["attendance"] < 75:
            reasons.append("Attendance below 75%")
        if r["backlogs"] > 0:
            reasons.append(f"{r['backlogs']} backlog(s)")
        if r["percentage"] < 50:
            reasons.append("Percentage below 50%")
        if reasons:
            needs_attention.append({**r, "reasons": reasons})
    return render(
        request, "admin_submissions.html",
        tracker=tracker, manual_records=manual_records,
        registered=len(tracker), submitted=submitted,
        pending=len(tracker) - submitted, total_records=len(records),
        completion=round(submitted / len(tracker) * 100) if tracker else 0,
        needs_attention=needs_attention, sections=events.list_sections(),
    )


@require_POST
def admin_delete_record(request, student_id):
    delete_student_record(student_id)
    messages.success(
        request,
        f"Record {student_id} was deleted. If it belonged to a student "
        "account, that student can submit again.",
    )
    return redirect("admin_submissions")


def _csv_safe(value):
    # stops Excel from running text such as "=1+1" typed by a student
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def admin_export(request):
    df = load_all_as_dataframe()
    df = df.astype(object).map(_csv_safe)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=students.csv"
    return response


def admin_events(request):
    return render(request, "admin_events.html", sections=events.list_sections())


@require_POST
def admin_event_add(request):
    try:
        events.add_section(request.POST.get("event_name"), request.POST.get("section_name"),
                           request.POST.get("description"))
        messages.success(request, "Section added.")
    except ValueError as error:
        messages.error(request, str(error))
    return redirect("admin_events")


def admin_event_detail(request, section_id):
    section = events.get_section(section_id)
    if section is None:
        return render_error(request, 404, "That section does not exist.")
    return render(request, "admin_event_detail.html", section=section,
                  people=events.participants(section_id))


@require_POST
def admin_event_delete(request, section_id):
    events.delete_section(section_id)
    messages.success(request, "Section and its registrations were deleted.")
    return redirect("admin_events")
