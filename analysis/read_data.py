"""Loads every saved student from the database (no Excel anywhere)."""


def load_data():
    from portal.records import load_all_as_dataframe
    return load_all_as_dataframe()


def clean_data(df):
    if df.empty:
        return df
    return df.drop_duplicates().dropna(how="all")
