from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import SupportCase


def get_all_cases(db: Session) -> List[SupportCase]:
    return db.query(SupportCase).all()


def get_case_by_id(db: Session, case_id: str) -> Optional[SupportCase]:
    return db.query(SupportCase).filter(SupportCase.case_id == case_id).first()
