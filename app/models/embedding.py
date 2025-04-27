# app/models/embedding.py
from sentence_transformers import SentenceTransformer
import numpy as np
from app.config import EMBEDDING_MODEL


class EmbeddingModel:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingModel, cls).__new__(cls)
            cls._instance.model = SentenceTransformer(EMBEDDING_MODEL)
        return cls._instance

    def encode(self, text: str) -> np.ndarray:
        """
        Generate embeddings for the given text
        """
        if not text or not text.strip():
            return np.zeros(self.model.get_sentence_embedding_dimension())

        return self.model.encode(text)

    def batch_encode(self, texts: list[str]) -> np.ndarray:
        """
        Generate embeddings for a batch of texts
        """
        if not texts:
            return np.array([])

        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]

        if not valid_texts:
            dim = self.model.get_sentence_embedding_dimension()
            return np.zeros((len(texts), dim))

        return self.model.encode(valid_texts)

    def get_dimension(self) -> int:
        """
        Return the dimension of the embeddings
        """
        return self.model.get_sentence_embedding_dimension()