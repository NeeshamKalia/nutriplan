"""Tests for RAG chunking, intent routing, and grounded answers."""

from unittest.mock import AsyncMock, patch

import pytest

from app.ai.rag_service import format_rag_response
from app.ai.text_utils import chunk_text, strip_html
from app.whatsapp.intent_classifier import classify_intent


def test_strip_html_removes_tags():
    assert strip_html("<p>Hello <strong>world</strong></p>") == "Hello world"


def test_chunk_text_splits_long_content():
    text = "Paragraph one.\n\n" + ("Word " * 200)
    chunks = chunk_text(text, chunk_size=200, overlap=20)
    assert len(chunks) >= 2
    assert all(len(chunk) <= 200 for chunk in chunks)


def test_classify_question_intent():
    assert classify_intent("What foods help with thyroid?") == "question"
    assert classify_intent("How much protein should I eat?") == "question"
    assert classify_intent("Can I eat rice at night?") == "question"
    assert classify_intent("help") == "command_help"
    assert classify_intent("today") == "command_today"


def test_format_rag_response_includes_sources():
    message = format_rag_response(
        "Turmeric may support thyroid health.",
        [{"title": "Thyroid Tips", "slug": "thyroid-tips"}],
        dietitian_slug="dr-neha",
    )
    assert "Turmeric may support thyroid health." in message
    assert "Thyroid Tips" in message
    assert "/p/dr-neha/thyroid-tips" in message


@pytest.mark.asyncio
async def test_answer_from_articles_uses_retrieved_context():
    from app.ai import rag_service
    from app.config import settings

    mock_chunks = [
        {
            "chunk_text": "Moringa is rich in iron and supports energy.",
            "chunk_index": 0,
            "title": "Iron Rich Foods",
            "slug": "iron-rich-foods",
            "similarity": 0.82,
        }
    ]

    with (
        patch.object(settings, "GEMINI_API_KEY", "test-key"),
        patch.object(rag_service, "embed_query", new=AsyncMock(return_value=[0.1] * 768)),
        patch(
            "app.ai.rag_service.search_relevant_chunks",
            new=AsyncMock(return_value=mock_chunks),
        ),
        patch(
            "app.ai.rag_service._generate_answer",
            new=AsyncMock(return_value="Moringa can help with iron intake."),
        ),
    ):
        answer = await rag_service.answer_from_articles(
            db=AsyncMock(),
            dietitian_id="00000000-0000-0000-0000-000000000001",
            dietitian_slug="dr-neha",
            question="What helps with low iron?",
        )

    assert "Moringa can help with iron intake." in answer
    assert "Iron Rich Foods" in answer


@pytest.mark.asyncio
async def test_answer_from_articles_no_matches():
    from app.ai import rag_service
    from app.config import settings

    with (
        patch.object(settings, "GEMINI_API_KEY", "test-key"),
        patch.object(rag_service, "embed_query", new=AsyncMock(return_value=[0.1] * 768)),
        patch(
            "app.ai.rag_service.search_relevant_chunks",
            new=AsyncMock(return_value=[]),
        ),
    ):
        answer = await rag_service.answer_from_articles(
            db=AsyncMock(),
            dietitian_id="00000000-0000-0000-0000-000000000001",
            dietitian_slug="dr-neha",
            question="Random unrelated topic?",
        )

    assert "couldn't find anything" in answer.lower()
