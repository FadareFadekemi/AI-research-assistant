import requests
import feedparser
import xml.etree.ElementTree as ET
from typing import List, Dict
from crewai.tools import tool

PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
ARXIV_API = "http://export.arxiv.org/api/query"

@tool("search_pubmed")
def search_pubmed(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search PubMed for academic papers.
    Returns a list of dictionaries with metadata: title, authors, year, abstract, link, source.
    """
    ids = requests.get(
        PUBMED_SEARCH,
        params={"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"}
    ).json()["esearchresult"]["idlist"]

    if not ids:
        return []

    xml = requests.get(
        PUBMED_FETCH,
        params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}
    ).text

    root = ET.fromstring(xml)
    articles = []

    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID")
        title = article.findtext(".//ArticleTitle")
        abstract = " ".join(
            [a.text for a in article.findall(".//AbstractText") if a.text]
        )
        if not abstract:
            continue

        # Extract authors
        authors = []
        for a in article.findall(".//AuthorList/Author"):
            last = a.findtext("LastName")
            first = a.findtext("ForeName")
            if last and first:
                authors.append(f"{last} {first[0]}.")
        if not authors:
            authors = ["Unknown"]

        year = article.findtext(".//PubDate/Year")
        if not year:
            # fallback to MedlineDate
            medline_date = article.findtext(".//PubDate/MedlineDate", "Unknown")
            year = medline_date.split(" ")[0] if medline_date != "Unknown" else "Unknown"

        articles.append({
            "title": title,
            "authors": authors,
            "year": year,
            "abstract": abstract,
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "source": "PubMed"
        })

    return articles


@tool("search_arxiv")
def search_arxiv(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search Arxiv for academic papers.
    Returns a list of dictionaries with metadata: title, authors, year, abstract, link, source.
    """
    feed = feedparser.parse(
        requests.get(
            ARXIV_API,
            params={"search_query": query, "max_results": max_results}
        ).text
    )

    papers = []
    for e in feed.entries:
        authors = [a.name for a in e.authors] if hasattr(e, "authors") else ["Unknown"]
        papers.append({
            "title": e.title,
            "authors": authors,
            "year": e.published[:4],
            "abstract": e.summary,
            "link": e.link,
            "source": "arXiv"
        })
    return papers


def format_articles_for_agent(raw_articles: List[Dict]) -> List[Dict]:
    """
    Convert raw search results into the format expected by the literature_agent.
    """
    formatted = []
    for art in raw_articles:
        formatted.append({
            "title": art.get("title"),
            "authors": art.get("authors", ["Unknown"]),
            "year": art.get("year", "Unknown"),
            "abstract": art.get("abstract", ""),
            "link": art.get("link", ""),
            "source": art.get("source", "Unknown")
        })
    return formatted


