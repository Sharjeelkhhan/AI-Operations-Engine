from unittest.mock import patch

import pytest
from sqlalchemy import delete

from app.database import SessionLocal
from app.models import PolicyChunk
from app.services import retrieval_service
from app.services.embedding_service import EmbeddingError, embed_text


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


def test_embed_text_empty_raises():
    with pytest.raises(EmbeddingError):
        embed_text("")
    with pytest.raises(EmbeddingError):
        embed_text("   ")


@patch("app.services.retrieval_service.embed_text")
def test_search_returns_top_k_ordered(mock_embed, db):
    db.execute(delete(PolicyChunk))
    db.commit()

    fake_vec = [0.1] * 768
    mock_embed.return_value = fake_vec

    for i in range(3):
        db.add(PolicyChunk(
            source_file="test.md",
            section_title=f"Section {i}",
            chunk_index=i,
            chunk_text=f"text {i}",
            embedding=fake_vec,
            embedding_model="nomic-embed-text",
            created_at="2026-09-12",
        ))
    db.commit()

    results = retrieval_service.search(db, "test query", top_k=2)
    assert len(results) == 2
    assert all(isinstance(r.similarity, float) for r in results)

    db.execute(delete(PolicyChunk))
    db.commit()