from crewai import Task, Agent
from app.core.llm import get_llm

# Specialized Chat Agent
chat_agent = Agent(
    role="AIRA Chat Assistant",
    goal="Provide friendly greetings and explain AIRA's research capabilities.",
    backstory=(
        "You are AIRA (AI Research Assistant). You are professional, warm, and highly "
        "knowledgeable about research. You mention that you can help with: \n"
        "- Literature reviews (PubMed/ArXiv)\n"
        "- Statistical Analysis (Chi-Square, Cronbach's Alpha, Descriptive stats)\n"
        "- Data Visualizations (Bar plots, Pie charts, etc.)"
    ),
    llm=get_llm(),
    allow_delegation=False
)

async def run_chat_service(user_message: str):
    """Executes a conversational task when the orchestrator detects chat intent."""
    task = Task(
        description=f"Respond naturally to the user message: {user_message}",
        expected_output="A professional response as AIRA, including a list of capabilities if appropriate.",
        agent=chat_agent
    )
    
    # Executes the conversational response
    response = chat_agent.execute_task(task)
    return response.strip()