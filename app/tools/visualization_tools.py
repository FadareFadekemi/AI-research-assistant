import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from crewai.tools import tool


@tool
def countplot(
    data: list[dict] | dict | str,
    x: str,
    hue: str | None = None,
    filename: str = "outputs/plots/countplot.png"
):
    """
    Dumb visualization tool.
    Expects resolved, valid column names ONLY.
    """

    if isinstance(data, str):
        df = pd.read_csv(data) if data.endswith(".csv") else pd.read_excel(data)
    elif isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = pd.DataFrame(data)

    if x not in df.columns:
        raise ValueError(f"Column '{x}' not found in dataset")

    if hue and hue not in df.columns:
        raise ValueError(f"Hue column '{hue}' not found in dataset")

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    plt.figure(figsize=(8, 5))
    sns.countplot(data=df, x=x, hue=hue)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

    return {
        "type": "countplot",
        "x": x,
        "hue": hue,
        "file": filename
    }


@tool
def barplot(
    data: list[dict] | dict | str,
    x: str | None = None,
    y: str | None = None,
    hue: str | None = None,
    filename: str = "outputs/plots/barplot.png"
):
    """
    Generate a barplot for one or two columns.
    Supports optional grouping via `hue`.
    Accepts list[dict], dict, or CSV/Excel file.
    Saves plot to disk and returns metadata.
    """

    # Load data into DataFrame
    if isinstance(data, str):
        if data.endswith(".csv"):
            df = pd.read_csv(data)
        else:
            df = pd.read_excel(data)
    elif isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = pd.DataFrame(data)

    if df.empty:
        raise ValueError("barplot received empty data")

    # Resolve columns
    if not x:
        raise ValueError("barplot requires 'x' column")
    if x not in df.columns:
        raise ValueError(f"X column '{x}' not found in dataset")
    if y and y not in df.columns:
        raise ValueError(f"Y column '{y}' not found in dataset")
    if hue and hue not in df.columns:
        raise ValueError(f"Hue column '{hue}' not found in dataset")

    # Ensure output directory exists
    out_dir = os.path.dirname(filename)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    plt.figure(figsize=(8, 5))
    sns.barplot(data=df, x=x, y=y, hue=hue)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

    return {
        "type": "barplot",
        "x": x,
        "y": y,
        "hue": hue,
        "file": filename
    }



@tool
def piechart(
    data: list[dict] | dict | str,
    column: str | None = None,
    filename: str = "outputs/plots/piechart.png"
):
    """
    Generate a pie chart for a single categorical column.
    Accepts list[dict], dict, or CSV/Excel file.
    Saves plot to disk and returns metadata.
    """

    # Load data into DataFrame
    if isinstance(data, str):
        if data.endswith(".csv"):
            df = pd.read_csv(data)
        else:
            df = pd.read_excel(data)
    elif isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = pd.DataFrame(data)

    if df.empty:
        raise ValueError("piechart received empty data")

    if not column:
        raise ValueError("piechart requires a column")
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset")

    # Ensure output directory exists
    out_dir = os.path.dirname(filename)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    counts = df[column].value_counts()
    plt.figure(figsize=(6, 6))
    plt.pie(counts, labels=counts.index, autopct="%1.1f%%", startangle=90)
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

    return {
        "type": "piechart",
        "column": column,
        "file": filename
    }
