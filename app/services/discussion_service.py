import asyncio
import json
from crewai.task import Task
from app.agents.discussion import discussion_agent

async def run_discussion(findings: dict, literature: dict | None = None):
    prompt = {
        "findings": findings,
        "literature": literature
    }
    task = Task(
        description="Write a discussion section based on findings and literature",
        expected_output="A rigorous academic discussion section",
        agent=discussion_agent,
    )
    context = json.dumps(prompt, indent=2)
    return await asyncio.to_thread(discussion_agent.execute_task, task, context)
