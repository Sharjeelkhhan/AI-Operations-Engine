from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    country: str = Field(..., min_length=2, max_length=50)
    plan: str = Field(..., pattern=r"^(Starter|Pro|Business|Enterprise)$")

    model_config = ConfigDict(from_attributes=True)


class CustomerCreate(CustomerBase):
    customer_id: str = Field(..., pattern=r"^C\d{4}$")


class CustomerOut(CustomerBase):
    customer_id: str
    model_config = ConfigDict(from_attributes=True)


class SubscriptionBase(BaseModel):
    customer_id: str
    plan: str
    monthly_price: int = Field(..., ge=0)
    status: str = Field(..., pattern=r"^(active|cancelled|suspended|past_due)$")
    start_date: date
    renewal_date: date

    model_config = ConfigDict(from_attributes=True)


class SubscriptionOut(SubscriptionBase):
    subscription_id: str
    model_config = ConfigDict(from_attributes=True)


class PaymentBase(BaseModel):
    customer_id: str
    subscription_id: str
    amount: int = Field(..., ge=0)
    currency: str = Field(..., min_length=3, max_length=3)
    status: str = Field(..., pattern=r"^(successful|failed|pending)$")
    payment_date: date

    model_config = ConfigDict(from_attributes=True)


class PaymentOut(PaymentBase):
    payment_id: str
    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseModel):
    customer_id: str
    subscription_id: str
    amount: int = Field(..., ge=0)
    status: str = Field(..., pattern=r"^(paid|unpaid)$")
    invoice_date: date

    model_config = ConfigDict(from_attributes=True)


class InvoiceOut(InvoiceBase):
    invoice_id: str
    model_config = ConfigDict(from_attributes=True)


class SupportCaseBase(BaseModel):
    customer_id: str
    message: str = Field(..., min_length=5, max_length=2000)
    submitted_at: date

    model_config = ConfigDict(from_attributes=True)


class SupportCaseOut(SupportCaseBase):
    case_id: str
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    detail: str
    model_config = ConfigDict(from_attributes=True)


class ClaimExtraction(BaseModel):
    claim_type: Literal[
        "duplicate_charge",
        "unauthorized_transaction",
        "refund_request",
        "cancellation_dispute",
        "payment_failure",
        "invoice_mismatch",
        "other",
    ]
    claimed_amount: Optional[float] = None
    urgency: Literal["low", "medium", "high"]
    key_details: str