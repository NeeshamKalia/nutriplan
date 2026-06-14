"""SQLAlchemy model for the dietitians table."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Dietitian(Base):
    """Dietitian (the paying customer).

    Represents a nutritionist who uses the platform to manage clients,
    generate meal plans, and publish articles.
    """

    __tablename__ = "dietitians"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    photo_url = Column(Text)
    bio = Column(Text)
    specializations = Column(ARRAY(Text))
    qualifications = Column(Text)
    practice_name = Column(String(255))

    # WhatsApp Business Account
    whatsapp_phone_number_id = Column(String(50))
    whatsapp_business_account_id = Column(String(50))
    whatsapp_access_token = Column(Text)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    clients = relationship("Client", back_populates="dietitian", lazy="selectin")
    refresh_tokens = relationship("RefreshToken", back_populates="dietitian")
    protocols = relationship("Protocol", back_populates="dietitian")
    articles = relationship("Article", back_populates="dietitian")
    food_items = relationship("FoodItem", back_populates="dietitian")
