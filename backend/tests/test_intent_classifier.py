import pytest
from app.whatsapp.intent_classifier import classify_intent

def test_classify_intent():
    assert classify_intent("today") == "command_today"
    assert classify_intent("what is aaj plan") == "command_today"
    assert classify_intent("done with lunch") == "command_done"
    assert classify_intent("✅") == "command_done"
    assert classify_intent("send grocery list") == "command_grocery"
    assert classify_intent("help please") == "command_help"
    assert classify_intent("?") == "command_help"
    assert classify_intent("swap this item") == "command_swap"
    assert classify_intent("I don't have paneer") == "command_swap"
    assert classify_intent("hello how are you") == "unknown"
