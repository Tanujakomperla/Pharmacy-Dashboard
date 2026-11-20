import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

from analysis.read_data import load_data, clean_data



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

