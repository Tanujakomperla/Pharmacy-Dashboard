import sys
import os
import pandas as pd


# =========================================================
# PROJECT BASE DIRECTORY
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.append(BASE_DIR)


# =========================================================
# IMPORT DATA FUNCTIONS
# =========================================================

from analysis.read_data import load_data, clean_data


# =========================================================
# NUMERIC COLUMNS
# =========================================================

STATISTICAL_COLUMNS = [
    "Age",
    "Attendance %",
    "CGPA",
    "Medicinal Chemistry - II",
    "Industrial Pharmacy - I",
    "Pharmacology - II",
    "Pharmacognosy and Phytochemistry - II",
    "Pharmaceutical Jurisprudence",
    "Total Marks",
    "Percentage",
    "GPAT Mock Score",
    "Backlogs"
]


# =========================================================
# CALCULATE STATISTICS
# =========================================================

def calculate_statistics(df):

    statistics_data = {}

    for column in STATISTICAL_COLUMNS:

        # Check column exists
        if column not in df.columns:
            continue

        # Convert to numeric
        series = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        # Remove missing values
        series = series.dropna()

        # Skip empty columns
        if series.empty:
            continue

        # Calculate statistics
        statistics_data[column] = {

            "mean": round(
                float(series.mean()),
                2
            ),

            "median": round(
                float(series.median()),
                2
            ),

            "std": round(
                float(series.std()),
                2
            ),

            "min": round(
                float(series.min()),
                2
            ),

            "max": round(
                float(series.max()),
                2
            ),

            "count": int(
                series.count()
            ),

            "mode": [
                round(float(value), 2)
                for value in series.mode().tolist()
            ][:5]
        }

    return statistics_data


# =========================================================
# TEST THE FILE DIRECTLY
# =========================================================

if __name__ == "__main__":

    print("=" * 70)

    print(
        "PHARMACY STUDENT STATISTICAL ANALYSIS"
    )

    print("=" * 70)


    # Load data

    df = load_data()


    # Clean data

    df = clean_data(df)


    print(
        "\nDataset Shape:",
        df.shape
    )


    # Calculate statistics

    statistics_data = calculate_statistics(df)


    print(
        "\nSTATISTICAL RESULTS"
    )

    print("=" * 70)


    # Display results

    for column, values in statistics_data.items():

        print(
            f"\n{column}"
        )

        print(
            f"Mean     : {values['mean']}"
        )

        print(
            f"Median   : {values['median']}"
        )

        print(
            f"Std Dev  : {values['std']}"
        )

        print(
            f"Minimum  : {values['min']}"
        )

        print(
            f"Maximum  : {values['max']}"
        )

        print(
            f"Count    : {values['count']}"
        )


    print("\n")

    print("=" * 70)

    print(
        "STATISTICS CALCULATION COMPLETED"
    )

    print("=" * 70)