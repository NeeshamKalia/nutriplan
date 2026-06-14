"""SQLAlchemy model for the food_items table."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class FoodItem(Base):
    """Indian food database entry with nutritional information.

    NULL dietitian_id = system-wide item (seeded data).
    Non-null dietitian_id = custom item added by a specific dietitian.

    Uses Indian food names (dal, roti, sabzi) alongside Hindi names.
    """

    __tablename__ = "food_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dietitian_id = Column(
        UUID(as_uuid=True), ForeignKey("dietitians.id"), nullable=True, index=True
    )

    name = Column(String(255), nullable=False)
    name_hindi = Column(String(255))
    category = Column(String(100), index=True)
    subcategory = Column(String(100))

    # Per 100g values
    calories_per_100g = Column(Integer)
    protein_per_100g = Column(Numeric(5, 1))
    carbs_per_100g = Column(Numeric(5, 1))
    fat_per_100g = Column(Numeric(5, 1))
    fiber_per_100g = Column(Numeric(5, 1))

    # Common serving
    default_serving_description = Column(String(100))
    default_serving_grams = Column(Numeric(6, 1))

    # Metadata
    is_vegetarian = Column(Boolean, default=True)
    is_vegan = Column(Boolean, default=False)
    is_gluten_free = Column(Boolean, default=False)
    common_allergens = Column(ARRAY(Text))

    # Approximate cost
    approx_cost_per_kg_inr = Column(Integer)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    dietitian = relationship("Dietitian", back_populates="food_items")
