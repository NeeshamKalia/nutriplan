"""SQLAlchemy model for the protocols table."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Protocol(Base):
    """Dietitian's saved meal plan template/protocol.

    Protocols define nutritional guidelines for specific conditions
    (e.g., "PCOS Weight Loss - Moderate Activity") that the AI uses
    as a starting point for plan generation.
    """

    __tablename__ = "protocols"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dietitian_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dietitians.id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String(255), nullable=False)
    description = Column(Text)
    target_conditions = Column(ARRAY(Text))
    target_goals = Column(ARRAY(Text))

    calorie_range_min = Column(Integer)
    calorie_range_max = Column(Integer)
    macro_split = Column(JSONB)

    general_guidelines = Column(Text)
    preferred_foods = Column(ARRAY(Text))
    avoided_foods = Column(ARRAY(Text))

    sample_plan = Column(JSONB)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    dietitian = relationship("Dietitian", back_populates="protocols")
