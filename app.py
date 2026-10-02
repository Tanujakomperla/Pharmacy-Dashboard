from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash
)
import pandas as pd
import numpy as np
import os

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error
)

from analysis.read_data import load_data, clean_data
from analysis.statistics import calculate_statistics
from analysis.correlation import calculate_correlations
from analysis.database import add_student, get_student_count


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

# Needed for flash() success/error banners. Fine to keep fixed for
# a small class project with no logins or sensitive sessions.
app.secret_key = os.environ.get("SECRET_KEY", "pharmacy-dashboard-secret-key")


# Minimum number of saved students before the prediction model
# will train. Below this, train/test split is unreliable.
MIN_STUDENTS_FOR_PREDICTION = 10


# ============================================================
# DATA / COLUMN CONFIGURATION
# ============================================================

SUBJECT_COLUMNS = [
    "Medicinal Chemistry - II",
    "Industrial Pharmacy - I",
    "Pharmacology - II",
    "Pharmacognosy and Phytochemistry - II",
    "Pharmaceutical Jurisprudence"
]


# Prediction features
# We are NOT using Total Marks or subject marks because
# Percentage is directly related to those values.

PREDICTION_FEATURES = [
    "Attendance %",
    "GPAT Mock Score",
    "Backlogs",
    "Age"
]

PREDICTION_TARGET = "Percentage"


# ============================================================
# DATA LOADING
# ============================================================

def get_data():

    df = load_data()

    df = clean_data(df)

    return df


# ============================================================
# CONVERT NUMPY / PANDAS VALUES
# ============================================================

def safe_mean(series):
    """Mean that returns 0.0 instead of NaN when there is no data yet
    (e.g. before the first student has been added)."""

    numeric_series = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if numeric_series.empty:
        return 0.0

    return round(
        float(numeric_series.mean()),
        2
    )


def python_value(value):

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        return float(value)

    if pd.isna(value):
        return None

    return value


# ============================================================
# DATAFRAME TO RECORDS
# ============================================================

def dataframe_to_records(df):

    records = df.to_dict(
        orient="records"
    )

    cleaned_records = []

    for record in records:

        cleaned_record = {}

        for key, value in record.items():

            cleaned_record[key] = python_value(value)

        cleaned_records.append(
            cleaned_record
        )

    return cleaned_records


# ============================================================
# SUMMARY CALCULATION
# ============================================================

def get_summary(df):

    summary = {

        "total_students":
            int(len(df)),

        "average_cgpa":
            safe_mean(df["CGPA"]) if "CGPA" in df.columns else 0.0,

        "average_attendance":
            safe_mean(df["Attendance %"]) if "Attendance %" in df.columns else 0.0,

        "average_percentage":
            safe_mean(df["Percentage"]) if "Percentage" in df.columns else 0.0,

        "average_gpat_score":
            safe_mean(df["GPAT Mock Score"]) if "GPAT Mock Score" in df.columns else 0.0,

        "average_backlogs":
            safe_mean(df["Backlogs"]) if "Backlogs" in df.columns else 0.0,

        "total_backlogs":
            int(
                pd.to_numeric(
                    df["Backlogs"],
                    errors="coerce"
                ).sum()
            ) if "Backlogs" in df.columns and not df.empty else 0
    }


    # --------------------------------------------------------
    # GENDER DISTRIBUTION
    # --------------------------------------------------------

    gender_data = (
        df["Gender"]
        .value_counts()
        .to_dict()
    )

    summary["gender_distribution"] = {
        str(key): int(value)
        for key, value in gender_data.items()
    }


    # --------------------------------------------------------
    # INTERNSHIP DISTRIBUTION
    # --------------------------------------------------------

    internship_data = (
        df["Internship Status"]
        .value_counts()
        .to_dict()
    )

    summary["internship_distribution"] = {
        str(key): int(value)
        for key, value in internship_data.items()
    }


    # --------------------------------------------------------
    # PROJECT DISTRIBUTION
    # --------------------------------------------------------

    project_data = (
        df["Project Status"]
        .value_counts()
        .to_dict()
    )

    summary["project_distribution"] = {
        str(key): int(value)
        for key, value in project_data.items()
    }


    # --------------------------------------------------------
    # PLACEMENT DISTRIBUTION
    # --------------------------------------------------------

    placement_data = (
        df["Placement Status"]
        .value_counts()
        .to_dict()
    )

    summary["placement_distribution"] = {
        str(key): int(value)
        for key, value in placement_data.items()
    }


    return summary


# ============================================================
# COMMON TEMPLATE CONTEXT
# ============================================================

def common_context(df):

    summary = get_summary(df)

    return {

        "summary": summary,

        "total_students":
            summary["total_students"],

        "average_cgpa":
            summary["average_cgpa"],

        "average_attendance":
            summary["average_attendance"],

        "average_percentage":
            summary["average_percentage"],

        "average_gpat_score":
            summary["average_gpat_score"],

        "average_backlogs":
            summary["average_backlogs"],

        "total_backlogs":
            summary["total_backlogs"],

        "gender_labels":
            list(
                summary[
                    "gender_distribution"
                ].keys()
            ),

        "gender_values":
            list(
                summary[
                    "gender_distribution"
                ].values()
            ),

        "internship_labels":
            list(
                summary[
                    "internship_distribution"
                ].keys()
            ),

        "internship_values":
            list(
                summary[
                    "internship_distribution"
                ].values()
            ),

        "project_labels":
            list(
                summary[
                    "project_distribution"
                ].keys()
            ),

        "project_values":
            list(
                summary[
                    "project_distribution"
                ].values()
            ),

        "placement_labels":
            list(
                summary[
                    "placement_distribution"
                ].keys()
            ),

        "placement_values":
            list(
                summary[
                    "placement_distribution"
                ].values()
            )
    }


# ============================================================
# OVERVIEW
# ============================================================

@app.route("/")
def index():

    df = get_data()

    context = common_context(df)

    return render_template(
        "index.html",
        **context
    )


# ============================================================
# STUDENT INFORMATION
# ============================================================

@app.route("/students-information")
def students_information():

    df = get_data()

    context = common_context(df)

    records = dataframe_to_records(df)

    return render_template(
        "students_information.html",
        **context,
        students=records,
        student_data=records,
        columns=list(df.columns),
        genders=sorted(df["Gender"].dropna().unique().tolist()),
        internships=sorted(df["Internship Status"].dropna().unique().tolist()),
        projects=sorted(df["Project Status"].dropna().unique().tolist()),
        placements=sorted(df["Placement Status"].dropna().unique().tolist())
    )


# ============================================================
# ACADEMIC ANALYSIS
# ============================================================

@app.route("/academic-analysis")
def academic_analysis():

    df = get_data()

    context = common_context(df)


    # --------------------------------------------------------
    # SUBJECT AVERAGES
    # --------------------------------------------------------

    subject_averages = {}

    for subject in SUBJECT_COLUMNS:

        if subject in df.columns:

            subject_averages[subject] = safe_mean(df[subject])


    # --------------------------------------------------------
    # HIGHEST / LOWEST SUBJECT AVERAGE
    # --------------------------------------------------------

    if subject_averages:

        highest_subject = max(
            subject_averages,
            key=subject_averages.get
        )

        lowest_subject = min(
            subject_averages,
            key=subject_averages.get
        )

    else:

        highest_subject = None

        lowest_subject = None


    # --------------------------------------------------------
    # STUDENT MARKS
    # --------------------------------------------------------

    student_records = dataframe_to_records(
        df
    )


    return render_template(

        "academic_analysis.html",

        **context,

        subject_columns=SUBJECT_COLUMNS,

        subject_averages=subject_averages,

        subject_labels=list(
            subject_averages.keys()
        ),

        subject_values=list(
            subject_averages.values()
        ),

        highest_subject=highest_subject,

        lowest_subject=lowest_subject,

        students=student_records,

        student_data=student_records,

        # Names expected by academic_analysis.html
        academic_students=student_records,

        subjects=SUBJECT_COLUMNS,

        overall_cgpa=context["average_cgpa"],

        overall_percentage=context["average_percentage"],

        columns=list(df.columns)
    )


# ============================================================
# STATISTICS
# ============================================================

@app.route("/statistics")
def statistics():

    df = get_data()


    # Calculate all statistics
    statistics_data = calculate_statistics(
        df
    )


    return render_template(

        "statistics.html",

        statistics_data=statistics_data,

        # Name expected by statistics.html
        statistics=statistics_data,

        student_count=len(df)

    )


# ============================================================
# CORRELATION
# ============================================================

@app.route("/correlation")
def correlation():

    df = get_data()


    # Calculate correlation with Percentage
    correlation_data = calculate_correlations(
        df
    )


    # --------------------------------------------------------
    # SORT CORRELATION VALUES
    # --------------------------------------------------------

    sorted_correlations = dict(
        sorted(
            correlation_data.items(),
            key=lambda item: abs(item[1]),
            reverse=True
        )
    )


    correlation_labels = list(
        sorted_correlations.keys()
    )

    correlation_values = list(
        sorted_correlations.values()
    )


    # --------------------------------------------------------
    # STRONGEST CORRELATION
    # --------------------------------------------------------

    strongest_feature = None

    strongest_value = None


    if sorted_correlations:

        strongest_feature = (
            correlation_labels[0]
        )

        strongest_value = (
            correlation_values[0]
        )


    return render_template(

        "correlation.html",

        correlation_data=correlation_data,

        sorted_correlations=sorted_correlations,

        correlation_labels=correlation_labels,

        correlation_values=correlation_values,

        strongest_feature=strongest_feature,

        strongest_value=strongest_value,

        target="Percentage",

        target_variable="Percentage",

        student_count=len(df)

    )


# ============================================================
# PREDICTION
# ============================================================

@app.route(
    "/prediction",
    methods=["GET", "POST"]
)
def prediction():

    df = get_data()


    # --------------------------------------------------------
    # NOT ENOUGH DATA YET
    # --------------------------------------------------------
    # The regression model needs a reasonable number of students
    # before a train/test split means anything. Early on (right
    # after launch, or the first day of data entry) we skip
    # training instead of crashing or showing a meaningless model.

    if len(df) < MIN_STUDENTS_FOR_PREDICTION:

        return render_template(

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
                request.form.get(
                    "attendance"
                )
            )

            gpat_score = float(
                request.form.get(
                    "gpat_score"
                )
            )

            backlogs = float(
                request.form.get(
                    "backlogs"
                )
            )

            age = float(
                request.form.get(
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

    return render_template(

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


@app.route(
    "/add-student",
    methods=["GET", "POST"]
)
def add_student_page():

    if request.method == "POST":

        # Check every required field was actually filled in.
        missing = [
            field for field in ADD_STUDENT_REQUIRED_FIELDS
            if not request.form.get(field, "").strip()
        ]

        if missing:

            flash(
                "Please fill in every field before submitting.",
                "error"
            )

            return render_template(
                "add_student.html",
                form=request.form
            )

        try:

            new_id = add_student(request.form)

        except ValueError:

            flash(
                "Please enter valid numbers for age, marks, "
                "attendance, CGPA, GPAT score and backlogs.",
                "error"
            )

            return render_template(
                "add_student.html",
                form=request.form
            )

        flash(
            f"Saved! {request.form['student_name']} was added as "
            f"{new_id}. The dashboard now includes this record.",
            "success"
        )

        return redirect(
            url_for("students_information")
        )

    return render_template(
        "add_student.html",
        form={}
    )


# ============================================================
# API - COMPLETE DATA
# ============================================================

@app.route("/api/data")
def api_data():

    df = get_data()

    return jsonify(
        dataframe_to_records(df)
    )


# ============================================================
# API - SUMMARY
# ============================================================

@app.route("/api/summary")
def api_summary():

    df = get_data()

    return jsonify(
        get_summary(df)
    )


# ============================================================
# API - STATISTICS
# ============================================================

@app.route("/api/statistics")
def api_statistics():

    df = get_data()

    statistics_data = (
        calculate_statistics(df)
    )

    return jsonify(
        statistics_data
    )


# ============================================================
# API - CORRELATION
# ============================================================

@app.route("/api/correlation")
def api_correlation():

    df = get_data()

    correlation_data = (
        calculate_correlations(df)
    )

    return jsonify(
        correlation_data
    )


# ============================================================
# 404 HANDLER
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return """

    <h1>404 - Page Not Found</h1>

    <p>
        The requested page does not exist.
    </p>

    <p>
        <a href="/">
            Go to Dashboard
        </a>
    </p>

    """, 404


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    print("=" * 70)

    print(
        "PHARMACY STUDENT PERFORMANCE "
        "ANALYTICS DASHBOARD"
    )

    print("=" * 70)

    print(
        "Data source: SQLite database "
        "(data/students.db) - no Excel file"
    )

    print(
        f"Students currently saved: {get_student_count()}"
    )

    print()

    print(
        "Available Pages:"
    )

    print(
        "http://127.0.0.1:5000/"
    )

    print(
        "http://127.0.0.1:5000/students-information"
    )

    print(
        "http://127.0.0.1:5000/academic-analysis"
    )

    print(
        "http://127.0.0.1:5000/statistics"
    )

    print(
        "http://127.0.0.1:5000/correlation"
    )

    print(
        "http://127.0.0.1:5000/prediction"
    )

    print(
        "http://127.0.0.1:5000/add-student"
    )

    print("=" * 70)


    app.run(
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", 5000))
    )