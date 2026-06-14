"""SQLAlchemy model for the clients table."""

import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from app.database import Base


class Client(Base):
    """Client managed by a dietitian, interacts via WhatsApp.

    Multi-tenant: every query MUST filter by dietitian_id.
    Clients have no login — they are identified by WhatsApp number.
    """

    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dietitian_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dietitians.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name = Column(String(255), nullable=False)
    whatsapp_number = Column(String(20), nullable=False, index=True)
    email = Column(String(255))
    age = Column(Integer)
    gender = Column(String(20))
    height_cm = Column(Numeric(5, 1))
    weight_kg = Column(Numeric(5, 1))
    target_weight_kg = Column(Numeric(5, 1))
    activity_level = Column(String(50))

    # Health profile
    medical_conditions = Column(ARRAY(Text))
    allergies = Column(ARRAY(Text))
    food_preferences = Column(ARRAY(Text))
    cuisine_preference = Column(String(50))
    dietary_type = Column(String(50))

    # Goals & constraints
    primary_goal = Column(String(100))
    monthly_food_budget_inr = Column(Integer)
    daily_calorie_target = Column(Integer)
    meals_per_day = Column(Integer, default=5)
    meal_timing_preferences = Column(JSONB)

    # Additional notes
    notes = Column(Text)
    lifestyle_notes = Column(Text)

    # Status
    status = Column(String(20), default="active")
    archived_at = Column(DateTime(timezone=True))
    onboarded_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    dietitian = relationship("Dietitian", back_populates="clients")
    meal_plans = relationship("MealPlan", back_populates="client")
    meal_logs = relationship("MealLog", back_populates="client")
    progress_logs = relationship("ProgressLog", back_populates="client")

    __table_args__ = (
        UniqueConstraint("dietitian_id", "whatsapp_number", name="uq_client_whatsapp"),
    )
