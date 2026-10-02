import sys
import os
import pandas as pd


# ==========================================================
# PROJECT ROOT
# ==========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.append(BASE_DIR)


# ==========================================================
# IMPORT DATA FUNCTIONS
# ==========================================================

from analysis.read_data import load_data, clean_data


# ==========================================================
# TARGET COLUMN
# ==========================================================

TARGET_COLUMN = "Percentage"


# ==========================================================
# VARIABLES FOR CORRELATION
# ==========================================================

CORRELATION_COLUMNS = [

    "Age",

    "Attendance %",

    "CGPA",

    "Medicinal Chemistry - II",

    "Industrial Pharmacy - I",

    "Pharmacology - II",

    "Pharmacognosy and Phytochemistry - II",

    "Pharmaceutical Jurisprudence",

    "Total Marks",

    "GPAT Mock Score",

    "Backlogs"

]


# ==========================================================
# CALCULATE CORRELATION
# ==========================================================

def calculate_correlations(df):

    correlation_data = {}


    for column in CORRELATION_COLUMNS:

        if column not in df.columns:
            continue


        if TARGET_COLUMN not in df.columns:
            continue


        x = pd.to_numeric(
            df[column],
            errors="coerce"
        )


        y = pd.to_numeric(
            df[TARGET_COLUMN],
            errors="coerce"
        )


        valid_data = pd.concat(
            [x, y],
            axis=1
        ).dropna()


        if len(valid_data) < 2:
            continue


        correlation = valid_data.iloc[:, 0].corr(
            valid_data.iloc[:, 1]
        )


        correlation_data[column] = round(
            correlation,
            3
        )


    return correlation_data


# ==========================================================
# INTERPRET CORRELATION
# ==========================================================

def interpret_correlation(value):

    absolute_value = abs(value)


    if absolute_value >= 0.7:

        strength = "Strong"

    elif absolute_value >= 0.4:

        strength = "Moderate"

    elif absolute_value >= 0.2:

        strength = "Weak"

    else:

        strength = "Very Weak"


    if value > 0:

        direction = "Positive"

    elif value < 0:

        direction = "Negative"

    else:

        direction = "No"


    return f"{strength} {direction}"


# ==========================================================
# MAIN TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 75)

    print("PHARMACY STUDENT CORRELATION ANALYSIS")

    print("=" * 75)


    # ------------------------------------------------------
    # LOAD DATA
    # ------------------------------------------------------

    df = load_data()


    # ------------------------------------------------------
    # CLEAN DATA
    # ------------------------------------------------------

    df = clean_data(df)


    print("\nDataset Shape:")

    print(df.shape)


    # ------------------------------------------------------
    # CALCULATE CORRELATIONS
    # ------------------------------------------------------

    correlation_data = calculate_correlations(
        df
    )


    # ------------------------------------------------------
    # DISPLAY RESULTS
    # ------------------------------------------------------

    print("\nCORRELATION WITH PERCENTAGE")

    print("=" * 75)


    for column, value in correlation_data.items():

        interpretation = interpret_correlation(
            value
        )


        print(
            f"{column:<45} : {value:>7}   ({interpretation})"
        )


    print("\n")

    print("=" * 75)

    print(
        "Correlation calculation completed successfully!"
    )

    print("=" * 75)