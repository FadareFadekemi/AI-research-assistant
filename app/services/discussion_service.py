import json
import asyncio
from typing import List, Dict, Any
from crewai import Task
from app.agents.discussion import discussion_agent
from app.tools.literature_tools import search_pubmed, search_arxiv, format_articles_for_agent, _extract_search_keywords
from app.core.llm import get_llm

def _build_apa_reference(article: Dict) -> str:
    authors = article.get("authors", ["Unknown"])
    year = article.get("year", "n.d.")
    title = article.get("title", "")
    source = article.get("source", "")
    link = article.get("link", "")
    return f"{', '.join(authors)} ({year}). {title}. {source}. {link}"

def _format_sources_for_prompt(articles: List[Dict]) -> str:
    formatted = []
    for idx, art in enumerate(articles, start=1):
        formatted.append(
            f"SOURCE {idx}:\nTitle: {art['title']}\nAuthors: {', '.join(art['authors'])}\n"
            f"Year: {art['year']}\nAbstract: {art['abstract']}\n"
        )
    return "\n".join(formatted)

async def run_discussion_service(
    topic: str,
    findings: str,
    word_count: int = 1000,
    max_results: int = 8
) -> Dict[str, Any]:
    """
    Orchestrates search and LLM-synthesis to produce a narrative discussion.
    """
    # 1. Targeted Literature Retrieval
    search_query = await _extract_search_keywords(topic, findings)
    
    pubmed_task = asyncio.to_thread(search_pubmed.run, query=search_query, max_results=max_results)
    arxiv_task = asyncio.to_thread(search_arxiv.run, query=search_query, max_results=max_results)
    pubmed_results, arxiv_results = await asyncio.gather(pubmed_task, arxiv_task)
    
    articles = format_articles_for_agent((pubmed_results or []) + (arxiv_results or []))
    formatted_sources = _format_sources_for_prompt(articles) if articles else "No specific external literature found."

    # 2. Define the Narrative Task (Instructions injected here to avoid Agent errors)
    discussion_task = Task(
        description=(
            f"OBJECTIVE: Write a {word_count}-word academic Discussion section for: '{topic}'.\n\n"
            f"ANALYSIS RESULTS:\n{findings}\n\n"
            f"LITERATURE TO INTEGRATE:\n{formatted_sources}\n\n"
            "STRICT INSTRUCTIONS:\n"
            "1. THEMATIC NARRATIVE: Organize the discussion by thematic headings.\n"
            "2. INTEGRATED SYNTHESIS: Every paragraph must discuss a specific result and link it to a citation. "
            "Example: 'The data shows 85% use mobile money, which aligns with Okoro (2023) who found high digital adoption...'\n"
            "3. IN-TEXT CITATIONS: Use (Author, Year) format strictly.\n"
            "4. NO LISTS: The main discussion body must be in fluid academic paragraphs.\n"
            "5. OUTPUT: Return a JSON object: {'discussion_body': '...', 'implications': [], 'limitations': [], 'recommendations': [], 'references': []}"
        ),
        expected_output="A research-grade JSON object with narrative discussion and APA references.",
        agent=discussion_agent,
    )

    # 3. Execute Agent
    result_str = await asyncio.to_thread(discussion_agent.execute_task, task=discussion_task)
    
    # 4. Parse and Structure Output
    try:
        if "```json" in result_str:
            result_str = result_str.split("```json")[1].split("```")[0].strip()
        elif "```" in result_str:
            result_str = result_str.split("```")[1].split("```")[0].strip()
            
        discussion_data = json.loads(result_str)
        
        # Ensure references are never blank
        tool_refs = [_build_apa_reference(a) for a in articles]
        agent_refs = discussion_data.get("references", [])
        discussion_data["references"] = list(set(tool_refs + agent_refs))
        
        return discussion_data

    except Exception as e:
        return {
            "discussion_body": result_str,
            "references": [_build_apa_reference(a) for a in articles],
            "error": f"JSON parsing failed: {str(e)}"
        }