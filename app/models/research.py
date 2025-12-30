from pydantic import BaseModel
from typing import List, Dict, Optional


# ---------- Literature ----------

class LiteratureArticle(BaseModel):
    title: str
    year: str
    abstract: str
    link: str
    source: str


class LiteratureResponse(BaseModel):
    topic: str
    tone: str
    word_count: int

    theme_summary: str
    key_findings: List[str]
    research_gaps: List[str]

    references: List[str]
    articles: List[LiteratureArticle]


# ---------- Analysis ----------

class DescriptiveResult(BaseModel):
    counts: Dict[str, int]
    percentages: Dict[str, float]


class AnalysisResponse(BaseModel):
    descriptives: Dict[str, DescriptiveResult]
    statistics: Optional[Dict[str, float]] = None
    plots: List[Dict[str, str]]


# ---------- Discussion ----------

class DiscussionResponse(BaseModel):
    discussion: str
    implications: List[str]
    limitations: List[str]
    recommendations: List[str]
    references: List[str]


# ---------- Full Pipeline ----------

class FullPipelineResponse(BaseModel):
    literature: LiteratureResponse
    analysis: AnalysisResponse
    discussion: DiscussionResponse
