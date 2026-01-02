from crewai import Agent
from app.core.llm import get_llm
from app.tools.analysis_tools import descriptive_statistics
from app.tools.statistics_tools import chi_square_test, cronbach_alpha
from app.tools.visualization_tools import countplot, barplot, piechart
import pandas as pd
import os


def export_results_to_excel(results: dict, filename: str = "outputs/analysis_results.xlsx") -> str:
    """
    Convert nested analysis results dict into a readable Excel file.
    Each tool gets a separate sheet.
    Returns the path to the saved file.
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with pd.ExcelWriter(filename) as writer:
        for tool_name, result in results.items():
            try:
                # Attempt to convert result to DataFrame
                if isinstance(result, dict):
                    df = pd.DataFrame.from_dict(result, orient="index")
                elif isinstance(result, list):
                    df = pd.DataFrame(result)
                else:
                    # Fallback for simple outputs
                    df = pd.DataFrame({tool_name: [result]})
                df.to_excel(writer, sheet_name=tool_name[:31])  # Excel sheet name max 31 chars
            except Exception:
                # Skip non-convertible results
                continue
    return filename


analysis_agent = Agent(
    role="Data Analyst",
    goal=(
        "Understand the user's analytical intent and apply only the appropriate "
        "statistical methods and visualizations. "
        "When requested, export results to Excel for easier readability. "
        "Interpret results in plain language."
    ),
    backstory=(
        "You are a senior biostatistician. You always decide what analysis is appropriate "
        "based on the user's question. You never run unnecessary tests. "
        "You can generate Excel/CSV reports and interpret descriptive or inferential statistics in plain language."
    ),
    tools=[
        descriptive_statistics,
        chi_square_test,
        cronbach_alpha,
        countplot,
        barplot,
        piechart,
    ],
    llm=get_llm(),
    allow_delegation=False,
)
