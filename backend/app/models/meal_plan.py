"""SQLAlchemy models for meal plan tables.

Includes: MealPlan, MealPlanDay, MealPlanItem, MealPlanValidation.
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class MealPlan(Base):
    """A 7-day meal plan for a client.

    Lifecycle: draft → approved → delivered → expired
    """

    __tablename__ = "meal_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dietitian_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dietitians.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(255))
    week_start_date = Column(Date)
    status = Column(String(20), default="draft")

    # Generation metadata
    generation_prompt = Column(Text)
    generation_model = Column(String(100))
    generation_tokens_used = Column(Integer)
    generation_cost_usd = Column(Numeric(10, 6))
    generation_duration_ms = Column(Integer)
    custom_instructions = Column(Text)

    # Nutritional summary (calculated from items)
    avg_daily_calories = Column(Integer)
    avg_daily_protein_g = Column(Numeric(5, 1))
    avg_daily_carbs_g = Column(Numeric(5, 1))
    avg_daily_fat_g = Column(Numeric(5, 1))
    avg_daily_fiber_g = Column(Numeric(5, 1))

    # Protocol reference
    protocol_id = Column(UUID(as_uuid=True), ForeignKey("protocols.id"), nullable=True)

    approved_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    client = relationship("Client", back_populates="meal_plans")
    days = relationship(
        "MealPlanDay", back_populates="meal_plan", cascade="all, delete-orphan"
    )
    validations = relationship(
        "MealPlanValidation", back_populates="meal_plan", cascade="all, delete-orphan"
    )


class MealPlanDay(Base):
    """One day within a 7-day meal plan."""

    __tablename__ = "meal_plan_days"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meal_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_number = Column(Integer, nullable=False)
    day_label = Column(String(20))

    total_calories = Column(Integer)
    total_protein_g = Column(Numeric(5, 1))
    total_carbs_g = Column(Numeric(5, 1))
    total_fat_g = Column(Numeric(5, 1))
    total_fiber_g = Column(Numeric(5, 1))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    meal_plan = relationship("MealPlan", back_populates="days")
    items = relationship(
        "MealPlanItem", back_populates="meal_plan_day", cascade="all, delete-orphan"
    )


class MealPlanItem(Base):
    """A single meal/food item within a day.

    meal_type values: breakfast, mid_morning, lunch, evening_snack, dinner, bedtime
    """

    __tablename__ = "meal_plan_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_plan_day_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meal_plan_days.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    meal_type = Column(String(30), nullable=False)
    sort_order = Column(Integer, default=0)

    food_name = Column(String(255), nullable=False)
    food_name_hindi = Column(String(255))
    portion_description = Column(String(255))
    portion_grams = Column(Numeric(6, 1))

    calories = Column(Integer)
    protein_g = Column(Numeric(5, 1))
    carbs_g = Column(Numeric(5, 1))
    fat_g = Column(Numeric(5, 1))
    fiber_g = Column(Numeric(5, 1))

    # Link to food database (optional)
    food_item_id = Column(
        UUID(as_uuid=True), ForeignKey("food_items.id"), nullable=True
    )

    preparation_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    meal_plan_day = relationship("MealPlanDay", back_populates="items")


class MealPlanValidation(Base):
    """AI safety check results for a meal plan.

    validation_type: allergen_check, calorie_range, nutritional_balance, preference_compliance
    severity: error, warning, info
    """

    __tablename__ = "meal_plan_validations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meal_plans.id", ondelete="CASCADE"),
        nullable=False,
    )

    validation_type = Column(String(50), nullable=False)
    passed = Column(Boolean, nullable=False)
    severity = Column(String(20))
    message = Column(Text)
    details = Column(JSONB)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    meal_plan = relationship("MealPlan", back_populates="validations")
