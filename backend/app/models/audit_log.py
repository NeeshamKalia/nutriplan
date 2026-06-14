"""SQLAlchemy model for the audit_logs table.

Lightweight, append-only audit log for important SaaS events.
Uses ON DELETE SET NULL for dietitian_id so logs survive even if a dietitian is deleted.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class AuditLog(Base):
    """Tracks important events for debugging and compliance.

    Events: login, register, client_created, plan_generated,
    plan_approved, plan_delivered, etc.

    No FK relationship back to dietitian model — keeps it lightweight
    and allows logs to persist even if the dietitian account is deleted.
    """

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dietitian_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dietitians.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))

    metadata_ = Column("metadata", JSONB)  # 'metadata' is reserved in SQLAlchemy
    ip_address = Column(String(45))
    user_agent = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
