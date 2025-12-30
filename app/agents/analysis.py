from crewai import Agent
from app.core.llm import get_llm
from app.tools.analysis_tools import descriptive_statistics
from app.tools.statistics_tools import chi_square_test, cronbach_alpha
from app.tools.visualization_tools import countplot, barplot, piechart

# ------------------------
# Analysis Agent
# ------------------------
analysis_agent = Agent(
    role="Data Analyst",
    goal=(
        "Understand the user's analytical intent and apply only the appropriate "
        "statistical methods and visualizations."
    ),
    backstory=(
        "You are a senior biostatistician. You always decide what analysis is appropriate "
        "based on the user's question. You never run unnecessary tests. "
        "When requested, you interpret results of descriptive or inferential statistics using plain language."
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
