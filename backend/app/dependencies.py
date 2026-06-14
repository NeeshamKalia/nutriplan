"""FastAPI dependencies — authentication and database session."""

import uuid as uuid_mod

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import user_id_ctx
from app.database import get_db
from app.models.dietitian import Dietitian
from app.utils.security import decode_token

security = HTTPBearer()


async def get_current_dietitian(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Dietitian:
    """FastAPI dependency that extracts and validates the JWT access token.

    Returns the authenticated Dietitian model instance.
    Sets user_id in the logging context for request tracing.
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        dietitian_id = payload.get("sub")
        if not dietitian_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Convert string to UUID for the query
    try:
        did = uuid_mod.UUID(dietitian_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    result = await db.execute(
        select(Dietitian).where(Dietitian.id == did)
    )
    dietitian = result.scalar_one_or_none()
    if not dietitian:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Dietitian not found",
        )

    # Set user context for structured logging
    user_id_ctx.set(str(dietitian.id))

    return dietitian
