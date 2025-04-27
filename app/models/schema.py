# app/models/schema.py
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any


class WebPage(BaseModel):
    url: HttpUrl
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchQuery(BaseModel):
    query: str
    top_k: Optional[int] = 10


class SearchResult(BaseModel):
    url: HttpUrl
    title: str
    snippet: str
    relevance_score: float


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    semantic_understanding: str
    total_results: int
    execution_time: float