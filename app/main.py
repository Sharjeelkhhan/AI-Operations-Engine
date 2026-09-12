from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.routers import policy
from app.config import settings
from app.database import engine
from app.logger import logger
from app.rate_limit import rate_limiter
from app.routers import customers, payments, subscriptions, support_cases

app = FastAPI(title="NovaDesk AI Dispute Resolution System")

app.include_router(customers.router)
app.include_router(payments.router)
app.include_router(subscriptions.router)
app.include_router(support_cases.router)
app.include_router(policy.router)

def reset_rate_limit_history():
    rate_limiter.reset()


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.allow_request(client_ip):
        logger.warning("Rate limit exceeded for client %s", client_ip)
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."},
        )

    response = await call_next(request)
    logger.info(
        "request method=%s path=%s status=%s client=%s",
        request.method,
        request.url.path,
        response.status_code,
        client_ip,
    )
    return response


@app.get("/")
def root():
    return {"message": "NovaDesk AI API is running"}


@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as exc:
        logger.exception("Database health check failed")
        return {"status": "unhealthy", "error": str(exc)}