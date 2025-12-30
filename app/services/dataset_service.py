def describe_dataset(df):
    return {
        "columns": list(df.columns),
        "n_rows": df.shape[0],
        "n_columns": df.shape[1]
    }
