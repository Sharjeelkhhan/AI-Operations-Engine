from pydantic import BaseModel
from datetime import date
from typing import Optional

class CustomerOut(BaseModel):
    customer_id: str
    name: str
    email: str
    country: str
    plan: str
    class Config:
        orm_mode = True

class SubscriptionOut(BaseModel):
    subscription_id: str
    customer_id: str
    plan: str
    monthly_price: int
    status: str
    start_date: date
    renewal_date: date
    class Config:
        orm_mode = True

class PaymentOut(BaseModel):
    payment_id: str
    customer_id: str
    subscription_id: str
    amount: int
    currency: str
    status: str
    payment_date: date
    class Config:
        orm_mode = True

class InvoiceOut(BaseModel):
    invoice_id: str
    customer_id: str
    subscription_id: str
    amount: int
    status: str
    invoice_date: date
    class Config:
        orm_mode = True

class SupportCaseOut(BaseModel):
    case_id: str
    customer_id: str
    message: str
    submitted_at: date
    class Config:
        orm_mode = True