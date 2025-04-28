# app/main.py
from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import asyncio
import time
from typing import List, Optional
import os

from app.models.schema import SearchQuery, SearchResponse, WebPage
from app.services.search import SearchService
from app.services.crawler import WebCrawler
from app.services.vectordb import VectorDatabase
from app.utils.helpers import format_time, highlight_terms, truncate_text

from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="AI-Augmented Semantic Search Engine",
    description="A search engine that uses semantic text analysis to provide more relevant results",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Initialize services
search_service = SearchService()
crawler = WebCrawler()
vector_db = VectorDatabase()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Render the home page with search form
    """
    stats = vector_db.get_stats()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "stats": stats}
    )


@app.get("/search", response_class=HTMLResponse)
async def search_page(
        request: Request,
        q: str = Query(..., min_length=1),
        top_k: Optional[int] = Query(10, ge=1, le=50)
):
    """
    Perform a search and render results page
    """
    if not q:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Please enter a search query"}
        )

    start_time = time.time()

    # Create search query
    query = SearchQuery(query=q, top_k=top_k)

    # Perform search
    try:
        response = await search_service.search(query)

        # Highlight search terms in snippets
        terms = q.split()
        for result in response.results:
            result.snippet = highlight_terms(result.snippet, terms)

        execution_time = format_time(time.time() - start_time)

        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "response": response,
                "query": q,
                "execution_time": execution_time
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": f"Search error: {str(e)}"}
        )


@app.post("/api/search")
async def api_search(query: SearchQuery):
    """
    API endpoint for search
    """
    try:
        response = await search_service.search(query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/crawl")
async def api_crawl(url: str, max_pages: int = 10, max_depth: int = 2):
    """
    API endpoint to crawl a website and index its content
    """
    try:
        # Crawl the website
        pages = await crawler.crawl(url, max_pages=max_pages, max_depth=max_depth)

        if not pages:
            raise HTTPException(status_code=400, detail="No pages were crawled")

        # Add pages to vector database
        vector_db.add_webpages(pages)

        return {
            "status": "success",
            "message": f"Crawled and indexed {len(pages)} pages",
            "pages": [{"url": str(page.url), "title": page.title} for page in pages]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def api_stats():
    """
    API endpoint to get statistics about the search engine
    """
    try:
        stats = vector_db.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/clear")
async def api_clear():
    """
    API endpoint to clear the vector database
    """
    try:
        vector_db.clear()
        return {"status": "success", "message": "Vector database cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

# Add this endpoint to your existing FastAPI app in app/main.py
@app.post("/api/search_extended")
async def api_search_extended(query: str = Query(...), top_k: int = Query(10)):
    """
    API endpoint for extended search with external sources
    """
    try:
        search_query = SearchQuery(query=query, top_k=top_k)
        response = await search_service.search_with_external_sources(query, top_k)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
