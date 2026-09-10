from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
ROLE_HEADER = "X-User-Role"


def require_api_key(api_key: str | None = Security(API_KEY_HEADER)) -> str:
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key


def require_admin_role(
    api_key: str = Security(require_api_key),
    user_role: str | None = Header(default=None, alias=ROLE_HEADER),
) -> str:
    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing user role",
        )

    if user_role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    return api_key
