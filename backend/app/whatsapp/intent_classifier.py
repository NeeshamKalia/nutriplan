import re


def classify_intent(message: str) -> str:
    """Rule-based intent classification for WhatsApp messages."""
    msg_lower = message.strip().lower()

    if re.search(r"\b(done)\b", msg_lower) or "✅" in msg_lower:
        return "command_done"
    elif re.search(r"\b(help|\?)\b", msg_lower) or msg_lower == "?":
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

    return "unknown"
