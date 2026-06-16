"""Security utilities for JWT and password operations."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """Create a short-lived JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRATION_MINUTES
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token_value() -> str:
    """Generate a cryptographically secure random refresh token value.

    We don't use JWT for refresh tokens — instead we use a random string
    stored as a SHA-256 hash in the database.
    """
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    """SHA-256 hash of a token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token_for_dietitian(dietitian_id: str) -> str:
    """Create an access token with dietitian_id as subject."""
    return create_access_token({"sub": str(dietitian_id)})


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    return jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
