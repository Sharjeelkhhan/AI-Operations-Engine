from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import require_admin_role
from app.database import get_db
from app.services import retrieval_service

router = APIRouter(prefix="/policy", tags=["policy"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(5, ge=1, le=20)


class RetrievedChunkOut(BaseModel):
    chunk_id: int
    source_file: str
    section_title: str
    chunk_text: str
    similarity: float


@router.post("/search", response_model=list[RetrievedChunkOut])
def search_policy(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_role),
):
    results = retrieval_service.search(db, payload.query, payload.top_k)
    return [
        RetrievedChunkOut(
            chunk_id=r.chunk_id,
            source_file=r.source_file,
            section_title=r.section_title,
            chunk_text=r.chunk_text,
            similarity=r.similarity,
        )
        for r in results
    ]