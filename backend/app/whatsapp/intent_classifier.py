import re


def _looks_like_question(msg_lower: str) -> bool:
    """Detect free-form nutrition questions (not command keywords)."""
    if msg_lower in ("?", "help"):
        return False
    if msg_lower.endswith("?"):
        return True
    return bool(
        re.search(
            r"^(what|how|why|when|can|is|are|does|do|should|tell me)\b",
            msg_lower,
        )
    )


def classify_intent(message: str) -> str:
    """Rule-based intent classification for WhatsApp messages."""
    msg_lower = message.strip().lower()

    if re.search(r"\b(done)\b", msg_lower) or "✅" in msg_lower:
        return "command_done"
    elif msg_lower in ("help", "?", "commands") or re.search(r"^help\b", msg_lower):
        return "command_help"
    elif re.search(r"\b(swap|replace|i don'?t have|i dont have)\b", msg_lower):
        return "command_swap"
    elif re.search(
        r"\b(had|ate|skipped?|missed|instead|replaced|swapped|didn'?t eat|did not eat)\b",
        msg_lower,
    ):
        return "deviation"
    elif re.search(r"\b(today|aaj)\b", msg_lower):
        return "command_today"
    elif re.search(r"\b(grocery|list)\b", msg_lower):
        return "command_grocery"
    elif re.search(r"\b(weight)\b", msg_lower) or re.search(
        r"\b(\d+(\.\d+)?)\s*(kg|kilos|kgs)\b", msg_lower
    ):
        return "command_weight"
    elif _looks_like_question(msg_lower):
        return "question"

    return "unknown"
