"""SQLAlchemy model for the whatsapp_messages table."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class WhatsAppMessage(Base):
    """Log of all WhatsApp messages (inbound and outbound).

    Stores message content, AI processing results, and delivery status.
    """

    __tablename__ = "whatsapp_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True)
    dietitian_id = Column(
        UUID(as_uuid=True), ForeignKey("dietitians.id"), nullable=True
    )

    direction = Column(String(10), nullable=False)  # 'inbound', 'outbound'
    wa_message_id = Column(String(255))
    from_number = Column(String(20))
    to_number = Column(String(20))

    message_type = Column(String(20))  # 'text', 'template', 'interactive', 'image', 'document'
    message_body = Column(Text)
    template_name = Column(String(100))

    status = Column(String(20))  # 'sent', 'delivered', 'read', 'failed'
    error_message = Column(Text)

    # AI processing
    intent = Column(String(50))  # 'command_today', 'command_done', etc.
    ai_response = Column(Text)
    ai_model = Column(String(100))
    ai_tokens_used = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
