import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from crewai.tools import tool
from io import BytesIO

def _load_dataframe(data):
    if isinstance(data, str):
        if data.endswith(".csv"):
            return pd.read_csv(data)
        else:
            return pd.read_excel(data)
    elif isinstance(data, (list, dict)):
        # Handle list of dicts from records
        return pd.DataFrame(data)
    return pd.DataFrame(data)

def _save_or_buffer_plot(filename: str = None) -> dict:
    """Return metadata and in-memory file if needed."""
    buffer = None
    if not filename:
        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
    else:
        out_dir = os.path.dirname(filename)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        plt.savefig(filename)
    plt.close()
    return buffer

@tool
def countplot(data: list[dict] | dict | str,
              x: str,
              hue: str | None = None,
              filename: str | None = "outputs/plots/countplot.png"):
    """Generate a countplot for a categorical variable. Supports 'hue' for comparison."""
    df = _load_dataframe(data)
    
    # Cleaning inputs to match our cleaned dataframe columns
    x = x.strip() if x else x
    hue = hue.strip() if hue else None

    # Verification logging
    print(f"DEBUG: Generating Countplot - X: '{x}', Hue: '{hue}'")

    if x not in df.columns:
        raise ValueError(f"Column '{x}' not found in dataset. Available: {list(df.columns)}")
    
    plt.figure(figsize=(10, 6))
    
    # Ensure we don't pass hue if it's identical to x (prevents Seaborn errors)
    actual_hue = hue if (hue and hue in df.columns and hue != x) else None
    
    sns.countplot(data=df, x=x, hue=actual_hue)
    
    plt.title(f"Distribution of {x}" + (f" by {actual_hue}" if actual_hue else ""))
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    
    buffer = _save_or_buffer_plot(filename)
    result = {"type": "countplot", "x": x, "hue": actual_hue}
    if filename: result["file"] = filename
    return result

@tool
def barplot(data: list[dict] | dict | str,
            x: str,
            y: str | None = None,
            hue: str | None = None,
            filename: str | None = "outputs/plots/barplot.png"):
    """Generate a barplot for categorical vs. numerical variable. Supports 'hue'."""
    df = _load_dataframe(data)
    
    x = x.strip() if x else x
    y = y.strip() if y else None
    hue = hue.strip() if hue else None

    print(f"DEBUG: Generating Barplot - X: '{x}', Y: '{y}', Hue: '{hue}'")

    if x not in df.columns:
        raise ValueError(f"X column '{x}' not found.")
    
    plt.figure(figsize=(10, 6))
    
    actual_hue = hue if (hue and hue in df.columns and hue != x) else None
    
    # If no Y is provided, Seaborn barplot needs an estimator or it defaults to count-like behavior
    sns.barplot(data=df, x=x, y=y, hue=actual_hue)
    
    plt.title(f"{y if y else 'Count'} by {x}" + (f" and {actual_hue}" if actual_hue else ""))
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    
    buffer = _save_or_buffer_plot(filename)
    result = {"type": "barplot", "x": x, "y": y, "hue": actual_hue}
    if filename: result["file"] = filename
    return result

@tool
def piechart(data: list[dict] | dict | str,
             column: str,
             filename: str | None = "outputs/plots/piechart.png"):
    """Generate a pie chart for a categorical variable."""
    df = _load_dataframe(data)
    column = column.strip()

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found.")

    counts = df[column].value_counts()
    plt.figure(figsize=(8, 8))
    plt.pie(counts, labels=counts.index, autopct="%1.1f%%", startangle=90)
    plt.title(f"Proportion of {column}")
    plt.axis("equal")
    plt.tight_layout()
    
    buffer = _save_or_buffer_plot(filename)
    result = {"type": "piechart", "column": column}
    if filename: result["file"] = filename
    return result