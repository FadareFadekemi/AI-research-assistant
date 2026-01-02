from crewai import Agent
from app.core.llm import get_llm
from app.tools.literature_tools import (
    search_pubmed,
    search_arxiv,
)

literature_agent = Agent(
    role="Literature Review Agent",
    goal="Retrieve and synthesize academic literature using external databases only.",
    backstory="""
You are a strict academic researcher.

CRITICAL RULES:
- You NEVER write literature from memory.
- You MUST use literature search tools.
- If no sources are found, you must say so.
- Every claim must be grounded in retrieved papers.
""",
    tools=[
        search_pubmed,
        search_arxiv,
    ],
    llm=get_llm(),
    allow_delegation=False,
    verbose=True,
)
