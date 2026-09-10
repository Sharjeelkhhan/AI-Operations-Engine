from sqlalchemy import Column, String, Integer, Date, ForeignKey
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    country = Column(String, nullable=False)
    plan = Column(String, nullable=False)


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), index=True)
    subscription_id = Column(String, ForeignKey("subscriptions.subscription_id"), index=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, index=True, nullable=False)
    payment_date = Column(Date, index=True, nullable=False)
    version = Column(Integer, nullable=False, default=1)


class SupportCase(Base):
    __tablename__ = "support_cases"

    case_id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), index=True)
    message = Column(String, nullable=False)
    submitted_at = Column(Date, index=True, nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"

    subscription_id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), index=True)
    plan = Column(String, nullable=False)
    monthly_price = Column(Integer, nullable=False)
    status = Column(String, index=True, nullable=False)
    start_date = Column(Date, nullable=False)
    renewal_date = Column(Date, index=True, nullable=False)
    version = Column(Integer, nullable=False, default=1)


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), index=True)
    subscription_id = Column(String, ForeignKey("subscriptions.subscription_id"), index=True)
    amount = Column(Integer, nullable=False)
    status = Column(String, index=True, nullable=False)
    invoice_date = Column(Date, nullable=False)