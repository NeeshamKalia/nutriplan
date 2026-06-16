"""Authentication service — register, login, refresh, logout.

Implements secure JWT refresh token rotation with token family tracking.
All database queries filter by specific fields — no .all() calls.
"""

import re
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logger import get_logger, user_id_ctx
from app.models.audit_log import AuditLog
from app.models.dietitian import Dietitian
from app.models.refresh_token import RefreshToken
from app.schemas.auth import (
    AuthResponse,
    DietitianProfileUpdate,
    DietitianResponse,
    LoginRequest,
    RegisterRequest,
    WhatsAppSetupRequest,
)
from app.utils.security import (
    create_access_token_for_dietitian,
    create_refresh_token_value,
    hash_password,
    hash_token,
    verify_password,
)

logger = get_logger(__name__)


def _generate_slug(full_name: str) -> str:
    """Convert name to URL-safe slug: 'Dr. Neha Sharma' → 'dr-neha-sharma'."""
    slug = full_name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)  # Remove special chars
    slug = re.sub(r"\s+", "-", slug)  # Spaces to hyphens
    slug = re.sub(r"-+", "-", slug).strip("-")  # Collapse multiple hyphens
    return slug


async def _ensure_unique_slug(
    db: AsyncSession, base_slug: str, exclude_id=None
) -> str:
    """Ensure slug is unique, appending number if needed."""
    slug = base_slug
    counter = 1
    while True:
        stmt = select(Dietitian.id).where(Dietitian.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(Dietitian.id != exclude_id)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def _build_dietitian_response(dietitian: Dietitian) -> DietitianResponse:
    """Build DietitianResponse from model instance."""
    # Handle specializations which may be a list (PG ARRAY) or None/string (SQLite)
    specs = dietitian.specializations
    if isinstance(specs, str):
        specs = [s.strip() for s in specs.split(",")] if specs else None
    elif not isinstance(specs, list):
        specs = None

    return DietitianResponse(
        id=str(dietitian.id),
        email=dietitian.email,
        full_name=dietitian.full_name,
        slug=dietitian.slug,
        phone=dietitian.phone,
        photo_url=dietitian.photo_url,
        bio=dietitian.bio,
        specializations=specs,
        qualifications=dietitian.qualifications,
        practice_name=dietitian.practice_name,
        has_whatsapp_setup=bool(dietitian.whatsapp_phone_number_id),
    )


async def _store_refresh_token(
    db: AsyncSession, dietitian_id, raw_token: str
) -> None:
    """Store a hashed refresh token in the database."""
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_EXPIRATION_DAYS
    )
    refresh_record = RefreshToken(
        dietitian_id=dietitian_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(refresh_record)


def _build_auth_response(
    dietitian: Dietitian, access_token: str, refresh_token: str
) -> AuthResponse:
    """Build the full authentication response."""
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
        dietitian=_build_dietitian_response(dietitian),
    )


async def register(db: AsyncSession, data: RegisterRequest) -> AuthResponse:
    """Register a new dietitian.

    1. Check email uniqueness
    2. Hash password
    3. Generate unique slug from name
    4. Create dietitian record
    5. Store refresh token (as SHA-256 hash)
    6. Return tokens + profile
    """
    # Check email uniqueness
    result = await db.execute(
        select(Dietitian).where(Dietitian.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create dietitian
    slug = await _ensure_unique_slug(db, _generate_slug(data.full_name))
    dietitian = Dietitian(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        slug=slug,
        phone=data.phone,
    )
    db.add(dietitian)
    await db.flush()  # Get the generated ID

    # Set logging context
    user_id_ctx.set(str(dietitian.id))

    # Generate tokens
    access_token = create_access_token_for_dietitian(dietitian.id)
    refresh_token = create_refresh_token_value()
    await _store_refresh_token(db, dietitian.id, refresh_token)

    # Audit log
    db.add(
        AuditLog(
            dietitian_id=dietitian.id,
            action="register",
            entity_type="dietitian",
            entity_id=dietitian.id,
        )
    )

    await db.commit()
    await db.refresh(dietitian)

    logger.info("Dietitian registered", extra={"dietitian_id": str(dietitian.id)})
    return _build_auth_response(dietitian, access_token, refresh_token)


async def login(db: AsyncSession, data: LoginRequest) -> AuthResponse:
    """Authenticate dietitian with email + password.

    1. Find dietitian by email
    2. Verify password
    3. Store new refresh token
    4. Create audit log entry
    5. Return tokens + profile
    """
    result = await db.execute(
        select(Dietitian).where(Dietitian.email == data.email)
    )
    dietitian = result.scalar_one_or_none()

    if not dietitian or not verify_password(data.password, dietitian.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Set logging context
    user_id_ctx.set(str(dietitian.id))

    # Generate tokens
    access_token = create_access_token_for_dietitian(dietitian.id)
    refresh_token = create_refresh_token_value()
    await _store_refresh_token(db, dietitian.id, refresh_token)

    # Audit log
    db.add(
        AuditLog(
            dietitian_id=dietitian.id,
            action="login",
            entity_type="dietitian",
            entity_id=dietitian.id,
        )
    )

    await db.commit()

    logger.info("Dietitian logged in", extra={"dietitian_id": str(dietitian.id)})
    return _build_auth_response(dietitian, access_token, refresh_token)


async def refresh(db: AsyncSession, raw_refresh_token: str) -> AuthResponse:
    """Refresh an access token using a refresh token.

    Implements secure rotation:
    1. Hash the incoming token
    2. Look up in refresh_tokens
    3. If revoked → token theft detected → revoke ALL tokens for this dietitian
    4. If expired → reject
    5. Revoke old token, create new pair, link via replaced_by
    """
    token_hash = hash_token(raw_refresh_token)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # SECURITY: If token was already revoked, this could mean theft
    if token_record.revoked_at:
        logger.warning(
            "Revoked refresh token reused — possible theft, revoking all tokens",
            extra={"dietitian_id": str(token_record.dietitian_id)},
        )
        # Revoke ALL tokens for this dietitian
        all_tokens_result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.dietitian_id == token_record.dietitian_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        for t in all_tokens_result.scalars():
            t.revoked_at = datetime.now(timezone.utc)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
        )

    # Check expiry — make comparison timezone-safe
    expires_at = token_record.expires_at
    now_utc = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        # SQLite returns naive datetimes; treat them as UTC
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now_utc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Get dietitian
    result = await db.execute(
        select(Dietitian).where(Dietitian.id == token_record.dietitian_id)
    )
    dietitian = result.scalar_one_or_none()
    if not dietitian:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Dietitian not found",
        )

    # Rotate: revoke old, create new
    new_refresh = create_refresh_token_value()
    new_hash = hash_token(new_refresh)
    new_expires = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_EXPIRATION_DAYS
    )
    new_token_record = RefreshToken(
        dietitian_id=dietitian.id,
        token_hash=new_hash,
        expires_at=new_expires,
    )
    db.add(new_token_record)
    await db.flush()

    # Revoke old and link
    token_record.revoked_at = datetime.now(timezone.utc)
    token_record.replaced_by = new_token_record.id

    access_token = create_access_token_for_dietitian(dietitian.id)

    await db.commit()

    logger.info("Token refreshed", extra={"dietitian_id": str(dietitian.id)})
    return _build_auth_response(dietitian, access_token, new_refresh)


async def logout(db: AsyncSession, raw_refresh_token: str) -> None:
    """Logout by revoking the refresh token."""
    token_hash = hash_token(raw_refresh_token)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_record = result.scalar_one_or_none()

    if token_record and not token_record.revoked_at:
        token_record.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(
            "Dietitian logged out",
            extra={"dietitian_id": str(token_record.dietitian_id)},
        )


async def update_profile(
    db: AsyncSession, dietitian: Dietitian, data: DietitianProfileUpdate
) -> DietitianResponse:
    """Update the authenticated dietitian's practice profile."""
    updates = data.model_dump(exclude_unset=True)

    if "full_name" in updates and updates["full_name"] != dietitian.full_name:
        dietitian.full_name = updates["full_name"]
        dietitian.slug = await _ensure_unique_slug(
            db, _generate_slug(updates["full_name"]), exclude_id=dietitian.id
        )

    for field in ("phone", "photo_url", "bio", "qualifications", "practice_name"):
        if field in updates:
            setattr(dietitian, field, updates[field])

    if "specializations" in updates:
        dietitian.specializations = updates["specializations"]

    await db.commit()
    await db.refresh(dietitian)

    logger.info("Profile updated", extra={"dietitian_id": str(dietitian.id)})
    return _build_dietitian_response(dietitian)


async def setup_whatsapp(
    db: AsyncSession, dietitian: Dietitian, data: WhatsAppSetupRequest
) -> DietitianResponse:
    """Store per-dietitian WhatsApp Business API credentials."""
    dietitian.whatsapp_phone_number_id = data.whatsapp_phone_number_id
    dietitian.whatsapp_access_token = data.whatsapp_access_token
    if data.whatsapp_business_account_id:
        dietitian.whatsapp_business_account_id = data.whatsapp_business_account_id

    await db.commit()
    await db.refresh(dietitian)

    logger.info("WhatsApp setup saved", extra={"dietitian_id": str(dietitian.id)})
    return _build_dietitian_response(dietitian)
