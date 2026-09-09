from sqlalchemy import Column, String, Integer, Date, ForeignKey
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    country = Column(String)
    plan = Column(String)

class Subscription(Base):
    __tablename__ = "subscriptions"
    subscription_id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"))
    plan = Column(String)
    monthly_price = Column(Integer)
    status = Column(String)
    start_date = Column(Date)
    renewal_date = Column(Date)

class Payment(Base):
    __tablename__ = "payments"
    payment_id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"))
    subscription_id = Column(String, ForeignKey("subscriptions.subscription_id"))
    amount = Column(Integer)
    currency = Column(String)
    status = Column(String)
    payment_date = Column(Date)

class Invoice(Base):
    __tablename__ = "invoices"
    invoice_id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"))
    subscription_id = Column(String, ForeignKey("subscriptions.subscription_id"))
    amount = Column(Integer)
    status = Column(String)
    invoice_date = Column(Date)

class SupportCase(Base):
    __tablename__ = "support_cases"
    case_id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"))
    message = Column(String)
    submitted_at = Column(Date)