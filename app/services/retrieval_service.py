import time
from dataclasses import dataclass
from typing import List

from sqlalchemy.orm import Session

from app.logger import logger
from app.models import PolicyChunk
from app.services.embedding_service import embed_text


@dataclass
class RetrievedChunk:
    chunk_id: int
    source_file: str
    section_title: str
    chunk_text: str
    similarity: float


def search(db: Session, query: str, top_k: int = 5) -> List[RetrievedChunk]:
    """Search policy_chunks by cosine similarity to the query embedding."""
    start = time.time()

    query_vector = embed_text(query)

    rows = (
        db.query(
            PolicyChunk,
            (1 - PolicyChunk.embedding.cosine_distance(query_vector)).label("similarity"),
        )
        .order_by(PolicyChunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
        .all()
    )

    results = [
        RetrievedChunk(
            chunk_id=chunk.id,
            source_file=chunk.source_file,
            section_title=chunk.section_title,
            chunk_text=chunk.chunk_text,
            similarity=float(sim),
        )
        for chunk, sim in rows
    ]

    latency_ms = int((time.time() - start) * 1000)
    logger.info(
        "retrieval_success",
        extra={
            "query_length": len(query),
            "top_k": top_k,
            "results_count": len(results),
            "top_similarity": round(results[0].similarity, 4) if results else None,
            "latency_ms": latency_ms,
        },
    )
    return results