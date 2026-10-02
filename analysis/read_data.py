import pandas as pd

from analysis.database import init_db, load_all_as_dataframe


def load_data():
    """Load every student currently saved in the database.

    This replaces the old Excel file. The table starts empty, and
    each student added through the "Add Student" form is saved here
    immediately, so every page always reflects the latest data with
    no manual refresh or re-upload needed.
    """

    init_db()

    df = load_all_as_dataframe()

    return df


def clean_data(df):
    """Light cleanup. Data coming from the database is already
    typed and validated by the add-student form, so this just
    guards against duplicate or fully-empty rows."""

    if df.empty:
        return df

    df = df.drop_duplicates()

    df = df.dropna(how="all")

    return df


if __name__ == "__main__":

    print("=" * 70)
    print("PHARMACY STUDENT DATABASE")
    print("=" * 70)

    df = load_data()

    print("\nStudents stored:", len(df))

    if not df.empty:
        print("\nColumns:")
        for column in df.columns:
            print("-", column)

        print("\nFirst 5 records:")
        print(df.head().to_string(index=False))

    print("\n" + "=" * 70)
