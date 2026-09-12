import time
from typing import List

import ollama

from app.logger import logger

EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIM = 768


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


def embed_text(text: str) -> List[float]:
    """Generate a 768-dim embedding for a single text string."""
    if not text or not text.strip():
        raise EmbeddingError("Cannot embed empty text")

    start = time.time()
    try:
        response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)
        vector = response["embedding"]

        if len(vector) != EMBEDDING_DIM:
            raise EmbeddingError(
                f"Expected {EMBEDDING_DIM} dims, got {len(vector)}"
            )

        latency_ms = int((time.time() - start) * 1000)
        logger.info(
            "embedding_success",
            extra={
                "model": EMBEDDING_MODEL,
                "text_length": len(text),
                "latency_ms": latency_ms,
            },
        )
        return vector

    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        logger.error(
            "embedding_failure",
            extra={
                "model": EMBEDDING_MODEL,
                "text_length": len(text) if text else 0,
                "latency_ms": latency_ms,
                "error": str(e),
            },
        )
        if isinstance(e, EmbeddingError):
            raise
        raise EmbeddingError(str(e)) from e


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Embed a batch of texts. Returns one vector per input."""
    return [embed_text(t) for t in texts]