"""SQLAlchemy model for the progress_logs table."""

import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ProgressLog(Base):
    """Tracks client body measurements and weight over time.

    Logged via dashboard or WhatsApp. Unique per client per date.
    """

    __tablename__ = "progress_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    )
    log_date = Column(Date, nullable=False)
    weight_kg = Column(Numeric(5, 1))
    waist_cm = Column(Numeric(5, 1))
    hip_cm = Column(Numeric(5, 1))
    chest_cm = Column(Numeric(5, 1))
    notes = Column(Text)
    logged_via = Column(String(20), default="dashboard")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    client = relationship("Client", back_populates="progress_logs")

    __table_args__ = (
        UniqueConstraint("client_id", "log_date", name="uq_progress_client_date"),
    )
