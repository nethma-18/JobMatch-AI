import logging
import numpy as np
from typing import List, Optional, Union

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """
    Generates sentence embeddings using sentence-transformers.
    Model: all-MiniLM-L6-v2 (lightweight, no GPU needed, ~80MB)
    Auto-downloads on first use from HuggingFace.
    """

    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.MODEL_NAME)
            logger.info(f"✅ Embedding model loaded: {self.MODEL_NAME}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.model = None

    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """
        Encode text(s) into embeddings.
        Returns numpy array of shape (n_texts, 384).
        """
        if self.model is None:
            raise RuntimeError("Embedding model not loaded")

        if isinstance(texts, str):
            texts = [texts]

        # Clean texts
        texts = [self._clean(t) for t in texts]

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 10,
            convert_to_numpy=True,
            normalize_embeddings=True,   # L2-normalized for cosine similarity
        )
        return embeddings

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text. Returns 1D array of shape (384,)."""
        return self.encode([text])[0]

    def _clean(self, text: str) -> str:
        """Truncate and clean text for embedding."""
        if not text:
            return ""
        # Truncate to ~512 tokens (~2000 chars) — model limit
        return text[:3000].strip()

    def is_ready(self) -> bool:
        return self.model is not None


# Singleton
embedding_engine = EmbeddingEngine()