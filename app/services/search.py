# app/services/search.py
from typing import List, Dict, Any
import time
import asyncio
from app.services.vectordb import VectorDatabase
from app.services.processor import TextProcessor
from app.services.llm import LLMService
from app.models.schema import SearchResult, SearchResponse, SearchQuery
from app.config import TOP_K_RESULTS, SIMILARITY_THRESHOLD


class SearchService:
    def __init__(self):
        self.vector_db = VectorDatabase()
        self.processor = TextProcessor()
        self.llm_service = LLMService()

    async def search(self, query: SearchQuery) -> SearchResponse:
        """
        Perform a semantic search using the query
        """
        start_time = time.time()

        # Process the query
        original_query = query.query

        # Use LLM to enhance the query
        enhanced_query = await self.llm_service.enhance_query(original_query)

        # Generate query embedding
        query_embedding = self.processor.process_query(enhanced_query)

        # Search the vector database
        raw_results = self.vector_db.search(query_embedding, top_k=query.top_k or TOP_K_RESULTS)

        # Filter results by similarity threshold
        filtered_results = [
            result for result in raw_results
            if result["similarity_score"] >= SIMILARITY_THRESHOLD
        ]

        # Generate semantic understanding
        semantic_understanding = await self.llm_service.generate_semantic_understanding(original_query)

        # Format results
        search_results = []
        for result in filtered_results:
            # Extract a snippet from the document
            snippet = self._extract_snippet(result["document"], enhanced_query)

            search_results.append(
                SearchResult(
                    url=result["metadata"]["url"],
                    title=result["metadata"]["title"],
                    snippet=snippet,
                    relevance_score=result["similarity_score"]
                )
            )

        execution_time = time.time() - start_time

        return SearchResponse(
            results=search_results,
            query=original_query,
            semantic_understanding=semantic_understanding,
            total_results=len(search_results),
            execution_time=execution_time
        )

    def _extract_snippet(self, document: str, query: str, max_length: int = 200) -> str:
        """
        Extract a relevant snippet from the document based on the query
        """
        if not document:
            return ""

        # Simple approach: find the first occurrence of any query term
        query_terms = query.lower().split()

        # Find the position of the first query term in the document
        positions = []
        for term in query_terms:
            if len(term) < 3:  # Skip very short terms
                continue

            pos = document.lower().find(term)
            if pos != -1:
                positions.append(pos)

        if not positions:
            # If no terms found, return the beginning of the document
            return document[:max_length] + "..."

        # Start the snippet from the earliest position found
        start_pos = min(positions)

        # Try to start at the beginning of a sentence
        sentence_start = document.rfind('. ', 0, start_pos)
        if sentence_start != -1 and start_pos - sentence_start < 100:
            start_pos = sentence_start + 2

        # Ensure we don't start beyond the document length
        if start_pos >= len(document):
            start_pos = 0

        # Extract the snippet
        end_pos = start_pos + max_length
        if end_pos >= len(document):
            snippet = document[start_pos:]
        else:
            # Try to end at the end of a sentence
            sentence_end = document.find('. ', start_pos, end_pos + 20)
            if sentence_end != -1:
                end_pos = sentence_end + 1
            snippet = document[start_pos:end_pos] + "..."

        return snippet


# Add this method to the existing SearchService class in app/services/search.py
async def search_with_external_sources(self, query: str, top_k: int = 10) -> Dict[str, Any]:
    """
    Extended search that includes both vector search and external search results
    """
    # Create search query object
    search_query = SearchQuery(query=query, top_k=top_k)

    # Get vector search results
    vector_results = await self.search(search_query)

    # Structure the combined results
    return {
        "vector_results": vector_results,
        "query": query,
        "timestamp": time.time()
    }