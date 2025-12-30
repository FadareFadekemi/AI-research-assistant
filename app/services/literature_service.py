# app/services/literature_service.py

import asyncio
from crewai.task import Task
from app.agents.literature import literature_agent
from app.tools.literature_functions import search_pubmed, search_arxiv, format_articles_for_agent

async def run_literature_review(topic: str, word_count: int = 500, tone: str = "formal"):
    # 1. Fetch articles
    pubmed_results = search_pubmed(topic, max_results=5)
    arxiv_results = search_arxiv(topic, max_results=5)
    all_results = pubmed_results + arxiv_results
    if not all_results:
        return {"message": "No articles found for this topic."}

    # 2. Format articles for the agent
    formatted_results = format_articles_for_agent(all_results)

    # 3. Prepare agent input
    agent_input = {
        "topic": topic,
        "articles": formatted_results,
        "tone": tone,
        "word_count": word_count
    }

    # 4. Create and execute Task in one step
    task = Task(
        description=f"Conduct a literature review on '{topic}'",
        expected_output="A concise, formal literature review",
        agent=literature_agent,
        inputs=agent_input  
    )

    # 5. Execute the task in a separate thread
    review = await asyncio.to_thread(literature_agent.execute_task, task)

    # 6. Only return the clean final review text
    return {
        "literature_review": review.get("final_output") if isinstance(review, dict) else str(review)
    }
