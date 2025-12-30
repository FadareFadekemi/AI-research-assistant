from crewai.tools import tool
import pandas as pd

@tool
def descriptive_statistics(dataset_path: str) -> dict:
    """
    Generate descriptive statistics for a dataset at the given file path.
    Supports CSV and Excel files.
    """

    if dataset_path.endswith(".csv"):
        df = pd.read_csv(dataset_path)
    else:
        df = pd.read_excel(dataset_path)

    summary = {}

    for col in df.columns:
        vc = df[col].value_counts(dropna=False)
        summary[col] = {
            "counts": vc.to_dict(),
            "percentages": (vc / vc.sum() * 100).round(2).to_dict()
        }

    return summary
