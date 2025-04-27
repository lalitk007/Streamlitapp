# app/services/vectordb.py
import chromadb
from chromadb.config import Settings
import numpy as np
from typing import List, Dict, Any, Optional
import os
import uuid
from app.config import CHROMA_PERSIST_DIRECTORY
from app.models.schema import WebPage
from app.services.processor import TextProcessor


class VectorDatabase:
    def __init__(self):
        self.processor = TextProcessor()
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """
        Get or create the collection for storing document embeddings
        """
        try:
            return self.client.get_collection("semantic_search")
        except:
            return self.client.create_collection(
                name="semantic_search",
                metadata={"hnsw:space": "cosine"}
            )

    def add_webpage(self, webpage: WebPage) -> None:
        """
        Process a webpage and add it to the vector database
        """
        processed_data = self.processor.process_webpage(webpage)

        # Add each chunk to the collection
        for i, (chunk, embedding) in enumerate(zip(processed_data["chunks"], processed_data["embeddings"])):
            if not chunk:  # Skip empty chunks
                continue

            doc_id = f"{uuid.uuid4()}"

            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding.tolist()],
                documents=[chunk],
                metadatas=[{
                    "url": processed_data["url"],
                    "title": processed_data["title"],
                    "chunk_index": i,
                    "domain": processed_data["metadata"].get("domain", ""),
                    "crawled_at": processed_data["metadata"].get("crawled_at", 0)
                }]
            )

    def add_webpages(self, webpages: List[WebPage]) -> None:
        """
        Add multiple webpages to the vector database
        """
        for webpage in webpages:
            self.add_webpage(webpage)

    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar documents using the query embedding
        """
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )

        search_results = []

        if not results["documents"]:
            return []

        for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
        )):
            # Convert distance to similarity score (1 - distance for cosine)
            similarity_score = 1 - distance

            search_results.append({
                "document": doc,
                "metadata": metadata,
                "similarity_score": similarity_score
            })

        return search_results

    # app/services/vectordb.py (continued)
    def clear(self) -> None:
        """
        Clear all documents from the collection
        """
        try:
            self.client.delete_collection("semantic_search")
            self.collection = self._get_or_create_collection()
        except Exception as e:
            print(f"Error clearing collection: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database
        """
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "collection_name": "semantic_search",
                "persist_directory": CHROMA_PERSIST_DIRECTORY
            }
        except Exception as e:
            print(f"Error getting stats: {str(e)}")
            return {
                "document_count": 0,
                "collection_name": "semantic_search",
                "persist_directory": CHROMA_PERSIST_DIRECTORY,
                "error": str(e)
            }