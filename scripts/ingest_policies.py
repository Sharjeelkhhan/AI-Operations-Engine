"""Ingest policy markdown files into policy_chunks with embeddings."""
import re
from datetime import date
from pathlib import Path

from sqlalchemy import delete

from app.database import SessionLocal
from app.models import PolicyChunk
from app.services.embedding_service import (
    EMBEDDING_MODEL,
    EmbeddingError,
    embed_text,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"


def chunk_by_section(text: str) -> list[tuple[str, str]]:
    """Split markdown by '## ' headings. Returns [(section_title, body)]."""
    parts = re.split(r"^##\s+(.+)$", text, flags=re.MULTILINE)
    chunks = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if body:
            chunks.append((title, f"## {title}\n\n{body}"))
    return chunks


def ingest():
    db = SessionLocal()
    try:
        # Idempotent: clear existing chunks before re-inserting
        db.execute(delete(PolicyChunk))
        db.commit()

        total = 0
        for md_file in sorted(KNOWLEDGE_DIR.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            chunks = chunk_by_section(text)
            print(f"{md_file.name}: {len(chunks)} chunks")

            for idx, (title, body) in enumerate(chunks):
                try:
                    vector = embed_text(body)
                except EmbeddingError as e:
                    print(f"  FAILED chunk '{title}': {e}")
                    continue

                db.add(
                    PolicyChunk(
                        source_file=md_file.name,
                        section_title=title,
                        chunk_index=idx,
                        chunk_text=body,
                        embedding=vector,
                        embedding_model=EMBEDDING_MODEL,
                        created_at=date.today(),
                    )
                )
                total += 1

        db.commit()
        print(f"\nIngested {total} chunks total.")
    finally:
        db.close()


if __name__ == "__main__":
    ingest()