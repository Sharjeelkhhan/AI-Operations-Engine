from fastapi import FastAPI
from app.routers import customers, payments, subscriptions, support_cases

app = FastAPI(title="NovaDesk AI Dispute Resolution System")

app.include_router(customers.router)
app.include_router(payments.router)
app.include_router(subscriptions.router)
app.include_router(support_cases.router)

@app.get("/")
def root():
    return {"message": "NovaDesk AI API is running"}