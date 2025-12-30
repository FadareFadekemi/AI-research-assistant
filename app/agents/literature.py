from crewai import Agent
from app.core.llm import get_llm
from app.tools.literature_tools import search_pubmed, search_arxiv
from app.agents.prompts import literature_prompt  

literature_agent = Agent(
    role="Literature Reviewer",
    goal="Find, summarize, and synthesize academic literature",
    backstory="An experienced academic researcher.",
    tools=[search_pubmed, search_arxiv],
    llm=get_llm(),
    prompt=literature_prompt
)

