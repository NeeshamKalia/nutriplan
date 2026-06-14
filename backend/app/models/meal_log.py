"""SQLAlchemy model for the meal_logs table."""

import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class MealLog(Base):
    """Tracks whether a client completed, skipped, or deviated from a planned meal.

    Logged primarily via WhatsApp commands (DONE, deviation detection).
    """

    __tablename__ = "meal_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    )
    meal_plan_item_id = Column(
        UUID(as_uuid=True), ForeignKey("meal_plan_items.id"), nullable=True
    )

    log_date = Column(Date, nullable=False)
    meal_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False)  # 'completed', 'skipped', 'deviated'
    deviation_note = Column(Text)

    logged_via = Column(String(20), default="whatsapp")
    logged_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    client = relationship("Client", back_populates="meal_logs")

    __table_args__ = (
        # Index for efficient adherence queries by client + date
        {"comment": "Meal tracking logs from WhatsApp"},
    )
