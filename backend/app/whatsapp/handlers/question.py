"""WhatsApp handler for RAG-powered article Q&A."""

from app.ai.rag_service import answer_from_articles
from app.models.client import Client
from app.models.dietitian import Dietitian
from app.services.whatsapp_service import whatsapp_service
from sqlalchemy.ext.asyncio import AsyncSession


async def handle_question(
    db: AsyncSession,
    client: Client,
    dietitian: Dietitian,
    from_number: str,
    body: str,
) -> None:
    """Answer a client question using published article content."""
    answer = await answer_from_articles(
        db=db,
        dietitian_id=dietitian.id,
        dietitian_slug=dietitian.slug,
        question=body.strip(),
    )
    await whatsapp_service.send_text_message(
        from_number,
        answer,
        db=db,
        client_id=client.id,
        dietitian_id=dietitian.id,
    )
