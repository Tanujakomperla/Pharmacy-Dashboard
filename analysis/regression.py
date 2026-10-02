import sys
import os
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error
)


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
# FEATURES USED FOR PREDICTION
# ==========================================================
#
# We are NOT using:
# - Total Marks
# - Individual subject marks
# - CGPA
#
# because these are directly related to academic performance
# and can cause target leakage when predicting Percentage.
#
# Instead, we use:
# - Attendance %
# - GPAT Mock Score
# - Backlogs
# - Age
#
# ==========================================================

FEATURE_COLUMNS = [
    "Attendance %",
    "GPAT Mock Score",
    "Backlogs",
    "Age"
]


# ==========================================================
# TRAIN PREDICTION MODEL
# ==========================================================

def train_prediction_model(df):

    # ------------------------------------------------------
    # Required columns
    # ------------------------------------------------------

    required_columns = (
        FEATURE_COLUMNS +
        [TARGET_COLUMN]
    )


    # ------------------------------------------------------
    # Check whether all required columns exist
    # ------------------------------------------------------

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]


    if missing_columns:

        raise ValueError(
            "Missing columns in dataset: "
            + ", ".join(missing_columns)
        )


    # ------------------------------------------------------
    # Select required columns
    # ------------------------------------------------------

    model_df = df[
        required_columns
    ].copy()


    # ------------------------------------------------------
    # Convert columns to numeric
    # ------------------------------------------------------

    for column in required_columns:

        model_df[column] = pd.to_numeric(
            model_df[column],
            errors="coerce"
        )


    # ------------------------------------------------------
    # Remove rows containing missing values
    # ------------------------------------------------------

    model_df = model_df.dropna()


    # ------------------------------------------------------
    # Check data size
    # ------------------------------------------------------

    if len(model_df) < 10:

        raise ValueError(
            "Not enough valid records for prediction."
        )


    # ------------------------------------------------------
    # Input variables X
    # ------------------------------------------------------

    X = model_df[
        FEATURE_COLUMNS
    ]


    # ------------------------------------------------------
    # Target variable y
    # ------------------------------------------------------

    y = model_df[
        TARGET_COLUMN
    ]


    # ------------------------------------------------------
    # Split dataset
    # ------------------------------------------------------
    #
    # 80% → Training
    # 20% → Testing
    #
    # random_state=42 makes the result reproducible.
    #
    # ------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(

        X,
        y,

        test_size=0.20,

        random_state=42

    )


    # ======================================================
    # CREATE LINEAR REGRESSION MODEL
    # ======================================================

    model = LinearRegression()


    # ======================================================
    # TRAIN MODEL
    # ======================================================

    model.fit(
        X_train,
        y_train
    )


    # ======================================================
    # MAKE PREDICTIONS
    # ======================================================

    y_pred = model.predict(
        X_test
    )


    # ======================================================
    # MODEL PERFORMANCE
    # ======================================================

    r2 = r2_score(
        y_test,
        y_pred
    )


    mae = mean_absolute_error(
        y_test,
        y_pred
    )


    mse = mean_squared_error(
        y_test,
        y_pred
    )


    rmse = mse ** 0.5


    # ======================================================
    # MODEL COEFFICIENTS
    # ======================================================

    coefficients = {}


    for feature, coefficient in zip(
        FEATURE_COLUMNS,
        model.coef_
    ):

        coefficients[feature] = round(
            coefficient,
            4
        )


    # ======================================================
    # ACTUAL AND PREDICTED VALUES
    # ======================================================

    actual_values = [
        round(value, 2)
        for value in y_test.tolist()
    ]


    predicted_values = [
        round(value, 2)
        for value in y_pred
    ]


    # ======================================================
    # RETURN RESULTS
    # ======================================================

    return {

        "model": model,

        "features": FEATURE_COLUMNS,

        "r2": round(
            r2,
            4
        ),

        "mae": round(
            mae,
            4
        ),

        "mse": round(
            mse,
            4
        ),

        "rmse": round(
            rmse,
            4
        ),

        "intercept": round(
            model.intercept_,
            4
        ),

        "coefficients": coefficients,

        "actual_values": actual_values,

        "predicted_values": predicted_values

    }


# ==========================================================
# MAIN PROGRAM
# ==========================================================

if __name__ == "__main__":

    print("=" * 75)

    print(
        "PHARMACY STUDENT PERFORMANCE "
        "PREDICTION MODEL"
    )

    print("=" * 75)


    # ======================================================
    # LOAD DATA
    # ======================================================

    print("\nLoading dataset...")

    df = load_data()


    # ======================================================
    # CLEAN DATA
    # ======================================================

    print("Cleaning dataset...")

    df = clean_data(df)


    # ======================================================
    # DATASET INFORMATION
    # ======================================================

    print("\nDataset Shape:")

    print(df.shape)


    print("\nTarget Column:")

    print(TARGET_COLUMN)


    print("\nFeatures Used:")

    for feature in FEATURE_COLUMNS:

        print(
            "-",
            feature
        )


    # ======================================================
    # TRAIN MODEL
    # ======================================================

    print("\nTraining prediction model...")

    results = train_prediction_model(
        df
    )


    # ======================================================
    # MODEL PERFORMANCE
    # ======================================================

    print("\nMODEL PERFORMANCE")

    print("=" * 75)


    print(
        "R² Score:",
        results["r2"]
    )


    print(
        "MAE:",
        results["mae"]
    )


    print(
        "MSE:",
        results["mse"]
    )


    print(
        "RMSE:",
        results["rmse"]
    )


    print(
        "\nIntercept:",
        results["intercept"]
    )


    # ======================================================
    # MODEL COEFFICIENTS
    # ======================================================

    print("\nMODEL COEFFICIENTS")

    print("=" * 75)


    for feature, coefficient in (
        results["coefficients"].items()
    ):

        print(
            f"{feature:<45} : {coefficient}"
        )


    # ======================================================
    # ACTUAL VS PREDICTED
    # ======================================================

    print("\nACTUAL VS PREDICTED")

    print("=" * 75)


    for actual, predicted in zip(

        results["actual_values"],

        results["predicted_values"]

    ):

        print(
            f"Actual: {actual:>6.2f}"
            f"   Predicted: {predicted:>6.2f}"
        )


    # ======================================================
    # COMPLETION MESSAGE
    # ======================================================

    print("\n")

    print("=" * 75)

    print(
        "Regression model completed successfully!"
    )

    print("=" * 75)