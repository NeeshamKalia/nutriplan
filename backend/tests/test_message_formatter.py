"""Tests for WhatsApp message formatting."""

from types import SimpleNamespace

from app.whatsapp.message_formatter import format_grocery_list


def _item(food_name, portion_description, portion_grams=None):
    return SimpleNamespace(
        food_name=food_name,
        portion_description=portion_description,
        portion_grams=portion_grams,
    )


def test_grocery_list_aggregates_quantities_by_grams():
    plan = SimpleNamespace(
        days=[
            SimpleNamespace(
                items=[
                    _item("Moong Dal", "1 bowl", 150),
                    _item("Roti", "2 medium", 80),
                ]
            ),
            SimpleNamespace(
                items=[
                    _item("Moong Dal", "1 bowl", 150),
                    _item("Roti", "2 medium", 80),
                ]
            ),
        ]
    )

    msg = format_grocery_list(plan)

    assert "Moong Dal" in msg
    assert "300g total" in msg
    assert "Roti" in msg
    assert "160g total" in msg


def test_grocery_list_counts_repeated_portions():
    plan = SimpleNamespace(
        days=[
            SimpleNamespace(
                items=[
                    _item("Paneer", "100g", None),
                    _item("Paneer", "100g", None),
                ]
            ),
        ]
    )

    msg = format_grocery_list(plan)
    assert "2× 100g" in msg
