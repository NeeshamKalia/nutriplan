"""Tests for phone number normalization utility."""

import pytest

from app.utils.phone import normalize_phone, is_valid_e164


class TestNormalizePhone:
    """Test E.164 normalization for common Indian and international formats."""

    # ── Indian numbers ──────────────────────────────────────────

    def test_bare_10_digit_indian(self):
        assert normalize_phone("9876543210") == "+919876543210"

    def test_bare_10_digit_starting_with_6(self):
        assert normalize_phone("6123456789") == "+916123456789"

    def test_bare_10_digit_starting_with_7(self):
        assert normalize_phone("7890123456") == "+917890123456"

    def test_bare_10_digit_starting_with_8(self):
        assert normalize_phone("8765432109") == "+918765432109"

    def test_leading_zero(self):
        assert normalize_phone("09876543210") == "+919876543210"

    def test_91_prefix_no_plus(self):
        assert normalize_phone("919876543210") == "+919876543210"

    def test_plus_91_prefix(self):
        assert normalize_phone("+919876543210") == "+919876543210"

    def test_plus_91_with_spaces(self):
        assert normalize_phone("+91 98765 43210") == "+919876543210"

    def test_plus_91_with_dashes(self):
        assert normalize_phone("+91-9876-543-210") == "+919876543210"

    def test_plus_91_with_parens(self):
        assert normalize_phone("+91 (987) 654 3210") == "+919876543210"

    # ── International numbers ───────────────────────────────────

    def test_us_number_with_plus(self):
        assert normalize_phone("+1-555-123-4567") == "+15551234567"

    def test_uk_number_with_plus(self):
        assert normalize_phone("+44 20 7946 0958") == "+442079460958"

    # ── Edge cases ──────────────────────────────────────────────

    def test_whitespace_trimming(self):
        assert normalize_phone("  9876543210  ") == "+919876543210"

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            normalize_phone("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            normalize_phone("   ")

    def test_short_number_raises(self):
        with pytest.raises(ValueError, match="Cannot normalize"):
            normalize_phone("12345")

    def test_non_indian_bare_10_digit(self):
        """10-digit number not starting with 6-9 gets + prefix only."""
        result = normalize_phone("1234567890")
        assert result == "+1234567890"

    def test_plus_with_no_digits_raises(self):
        with pytest.raises(ValueError, match="Invalid phone number"):
            normalize_phone("+")

    def test_plus_with_invalid_country_code_raises(self):
        with pytest.raises(ValueError, match="Invalid E.164"):
            normalize_phone("+0123456789")


class TestIsValidE164:
    """Test E.164 format validation."""

    def test_valid_indian(self):
        assert is_valid_e164("+919876543210") is True

    def test_valid_us(self):
        assert is_valid_e164("+15551234567") is True

    def test_missing_plus(self):
        assert is_valid_e164("919876543210") is False

    def test_too_short(self):
        assert is_valid_e164("+12345") is False

    def test_starts_with_zero(self):
        assert is_valid_e164("+0123456789") is False

    def test_empty(self):
        assert is_valid_e164("") is False
