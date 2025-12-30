from crewai import Agent
from app.core.llm import get_llm
from app.agents.prompts import DISCUSSION_PROMPT

discussion_agent = Agent(
    role="Discussion Writer",
    goal="Produce a rigorous academic discussion section",
    backstory="A senior academic journal reviewer.",
    llm=get_llm(),
    system_prompt=DISCUSSION_PROMPT
)
