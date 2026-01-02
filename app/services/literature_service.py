import json
from typing import List, Dict, Optional
from app.tools.literature_tools import search_pubmed, search_arxiv,format_articles_for_agent
from app.core.llm import get_llm

llm = get_llm()


  
def _build_apa_reference(article: Dict) -> str:
    authors = article.get("authors", ["Unknown"])
    year = article.get("year", "n.d.")
    title = article.get("title", "")
    source = article.get("source", "")
    link = article.get("link", "")

    author_str = ", ".join(authors)
    return f"{author_str} ({year}). {title}. {source}. {link}"


def _format_sources_for_prompt(articles: List[Dict]) -> str:
    formatted = []
    for idx, art in enumerate(articles, start=1):
        formatted.append(
            f"""
SOURCE {idx}:
Title: {art['title']}
Authors: {', '.join(art['authors'])}
Year: {art['year']}
Abstract: {art['abstract']}
Link: {art['link']}
"""
        )
    return "\n".join(formatted)


async def run_literature_review(
    topic: str,
    word_count: int = 1000,
    max_results: int = 10,
    tone: str = "formal",
    sources: Optional[List[str]] = None
) -> Dict:
    """
    Runs literature tools first, then synthesizes a full literature review
    using an LLM based ONLY on retrieved sources.
    """

    #  Retrieve sources
    pubmed_results = search_pubmed.run(
        query=topic,
        max_results=max_results
    )
    arxiv_results = search_arxiv.run(
        query=topic,
        max_results=max_results
    )

    raw_articles = pubmed_results + arxiv_results
    if not raw_articles:
        return {
            "literature_review": "No relevant academic literature was found for the given research question.",
            "references": []
        }

    articles = format_articles_for_agent(raw_articles)

    #  Prepare sources for LLM
    formatted_sources = _format_sources_for_prompt(articles)

    # LLM synthesis (controlled & grounded)
    llm = get_llm()

    prompt = f"""
You are an academic research assistant.

TASK:
Write a comprehensive literature review based ONLY on the provided academic sources.

STRICT RULES:
- Use ONLY the provided articles. Do NOT add new sources.
- Do NOT invent citations.
- Synthesize ideas across studies instead of summarizing one paper at a time.
- Maintain an academic tone suitable for a peer-reviewed journal.
- Use APA-style in-text citations (Author, Year).
- If an author is unknown, use the article title and year.
- The total length MUST be approximately {word_count} words.

STRUCTURE:
- Coherent narrative paragraphs
- Logical flow of themes and findings
- Critical comparison where appropriate

OUTPUT FORMAT:
- Plain text literature review
- APA in-text citations embedded naturally
- End with a section titled "References" in APA format

SOURCES:
{formatted_sources}
"""

    response = await llm.ainvoke(prompt)

    # 🔹 Step 4: Build references list
    references = [_build_apa_reference(a) for a in articles]

    return {
        "literature_review": response.content.strip(),
        "references": references
    }
