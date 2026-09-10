from typing import List, Optional

from sqlalchemy.orm import Session

from app.logger import logger
from app.models import Customer


def get_all_customers(db: Session) -> List[Customer]:
    return db.query(Customer).all()


def get_customer_by_id(db: Session, customer_id: str) -> Optional[Customer]:
    logger.info(f"Fetching customer {customer_id}")
    return db.query(Customer).filter(Customer.customer_id == customer_id).first()


def count_customers(db: Session) -> int:
    return db.query(Customer).count()
