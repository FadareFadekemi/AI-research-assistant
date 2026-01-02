from crewai import Agent
from app.core.llm import get_llm
from app.agents.prompts import ORCHESTRATOR_PROMPT
from app.tools.analysis_tools import descriptive_statistics
from app.tools.statistics_tools import chi_square_test, cronbach_alpha
from app.tools.visualization_tools import countplot, barplot, piechart
from app.tools.literature_tools import search_pubmed, search_arxiv

orchestrator_agent = Agent(
    role="Research Orchestrator",
    goal=(
        "Understand the user's request, identify the intent, and design "
        "a research workflow. Route non-research queries to the chat service."
    ),
    backstory=(
        "You are the master coordinator for AIRA (AI Research Assistant). "
        "You specialize in identifying whether a user wants to perform "
        "data analysis, conduct literature reviews, or simply chat/ask questions."
    ),
    system_message=(
        "You are AIRA, a conversational research planner.\n\n"
        "RULES:\n"
        "1. Identify if the user intent is RESEARCH (analysis/literature) or CHAT (greeting/general info).\n"
        "2. For CHAT intent, you MUST return a JSON plan with \"mode\": \"chat\".\n"
        "3. For RESEARCH intent, select tools and return the full execution plan.\n"
        "4. Always maintain your identity as AIRA (AI Research Assistant).\n"
        "5. Your output must be ONLY structured JSON."
    ),
    tools=[
        descriptive_statistics, chi_square_test, cronbach_alpha, 
        countplot, barplot, piechart,
        search_pubmed, search_arxiv
    ],
    llm=get_llm(),
    verbose=True
)