"""SQLAlchemy model for the refresh_tokens table.

Implements secure JWT refresh token rotation with token family tracking.
Tokens are stored as SHA-256 hashes — the raw token is never persisted.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class RefreshToken(Base):
    """Refresh token for secure JWT rotation.

    Security model:
    - Raw token is never stored — only SHA-256 hash
    - Each token is single-use: on refresh, old is revoked, new is issued
    - Token family tracking via `replaced_by` enables theft detection:
      if a revoked token is reused, revoke the entire family
    """

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dietitian_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dietitians.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True))
    replaced_by = Column(
        UUID(as_uuid=True), ForeignKey("refresh_tokens.id"), nullable=True
    )
    user_agent = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    dietitian = relationship("Dietitian", back_populates="refresh_tokens")
