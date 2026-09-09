import csv
from datetime import datetime
from app.database import SessionLocal
from app.models import Customer, Subscription, Payment, Invoice, SupportCase

def load_csv(filename, model, date_columns=[]):
    with open(f"data/{filename}", newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            for col in date_columns:
                if row[col]:
                    row[col] = datetime.strptime(row[col], "%Y-%m-%d").date()
            rows.append(model(**row))
    return rows

db = SessionLocal()

# Load customers
customers = load_csv("customers.csv", Customer)
db.add_all(customers)
db.commit()

# Load subscriptions
subscriptions = load_csv("subscriptions.csv", Subscription, date_columns=["start_date", "renewal_date"])
db.add_all(subscriptions)
db.commit()

# Load payments
payments = load_csv("payments.csv", Payment, date_columns=["payment_date"])
db.add_all(payments)
db.commit()

# Load invoices
invoices = load_csv("invoices.csv", Invoice, date_columns=["invoice_date"])
db.add_all(invoices)
db.commit()

# Load support cases
support_cases = load_csv("support_cases.csv", SupportCase, date_columns=["submitted_at"])
db.add_all(support_cases)
db.commit()

db.close()
print("Data loaded successfully.")