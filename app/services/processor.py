# app/services/processor.py
import re
from typing import List, Dict, Any
import numpy as np
from app.models.schema import WebPage
from app.models.embedding import EmbeddingModel


class TextProcessor:
    def __init__(self):
        self.embedding_model = EmbeddingModel()

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text by removing extra whitespace, special characters, etc.
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)

        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)

        # Remove special characters and digits
        text = re.sub(r'[^\w\s]', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            if end >= len(text):
                chunks.append(text[start:])
                break

            # Try to find a space to break at
            while end > start and text[end] != ' ':
                end -= 1

            if end == start:  # No space found, just cut at chunk_size
                end = start + chunk_size

            chunks.append(text[start:end])
            start = end - overlap

        return chunks

    def process_webpage(self, webpage: WebPage) -> Dict[str, Any]:
        """
        Process a webpage by chunking content and generating embeddings
        """
        processed_text = self.preprocess_text(webpage.content)
        chunks = self.chunk_text(processed_text)

        # Generate embeddings for each chunk
        embeddings = [self.embedding_model.encode(chunk) for chunk in chunks]

        return {
            "url": str(webpage.url),
            "title": webpage.title,
            "chunks": chunks,
            "embeddings": embeddings,
            "metadata": webpage.metadata
        }

    def process_query(self, query: str) -> np.ndarray:
        """
        Process a search query and generate embedding
        """
        processed_query = self.preprocess_text(query)
        query_embedding = self.embedding_model.encode(processed_query)

        return query_embedding