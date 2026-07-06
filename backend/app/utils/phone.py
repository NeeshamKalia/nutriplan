"""Phone number normalization utilities.

WhatsApp identifies clients by phone number, so consistent formatting is
critical. This module normalizes all phone numbers to E.164 format
(e.g., +919876543210) before storage and lookup.

Supports common Indian input formats:
  - 9876543210       → +919876543210  (bare 10-digit)
  - 09876543210      → +919876543210  (leading zero)
  - 919876543210     → +919876543210  (country code, no +)
  - +919876543210    → +919876543210  (already E.164)
  - +1 (555) 123-4567 → +15551234567  (international with formatting)
"""

import re


# Strip everything except digits and leading +
_STRIP_RE = re.compile(r"[^\d+]")

# Indian phone: 10 digits, optionally prefixed with 0 or 91 or +91
_INDIA_BARE_RE = re.compile(r"^[6-9]\d{9}$")  # 10-digit starting 6-9
_INDIA_ZERO_RE = re.compile(r"^0([6-9]\d{9})$")  # leading 0
_INDIA_CC_RE = re.compile(r"^91([6-9]\d{9})$")  # 91 prefix, no +

DEFAULT_COUNTRY_CODE = "91"  # India


def normalize_phone(raw: str) -> str:
    """Normalize a phone number to E.164 format.

    Args:
        raw: Raw phone number string in any common format.

    Returns:
        E.164 formatted string (e.g., "+919876543210").

    Raises:
        ValueError: If the number cannot be normalized.

    Examples:
        >>> normalize_phone("9876543210")
        '+919876543210'
        >>> normalize_phone("+91 98765 43210")
        '+919876543210'
        >>> normalize_phone("09876543210")
        '+919876543210'
        >>> normalize_phone("+1-555-123-4567")
        '+15551234567'
    """
    if not raw or not raw.strip():
        raise ValueError("Phone number cannot be empty.")

    # Preserve leading + before stripping
    has_plus = raw.strip().startswith("+")
    cleaned = _STRIP_RE.sub("", raw.strip())

    if not cleaned:
        raise ValueError(f"Invalid phone number: '{raw}'")

    # Already has + prefix → already has country code
    if has_plus:
        # cleaned may still contain the + character, strip it
        digits = cleaned.lstrip("+")
        return f"+{digits}"

    # Bare 10-digit Indian number (starts with 6-9)
    if _INDIA_BARE_RE.match(cleaned):
        return f"+{DEFAULT_COUNTRY_CODE}{cleaned}"

    # Leading zero (domestic Indian format)
    zero_match = _INDIA_ZERO_RE.match(cleaned)
    if zero_match:
        return f"+{DEFAULT_COUNTRY_CODE}{zero_match.group(1)}"

    # 91 prefix without + (e.g., "919876543210")
    cc_match = _INDIA_CC_RE.match(cleaned)
    if cc_match:
        return f"+{DEFAULT_COUNTRY_CODE}{cc_match.group(1)}"

    # Fallback: assume digits include country code, just add +
    if len(cleaned) >= 10:
        return f"+{cleaned}"

    raise ValueError(
        f"Cannot normalize phone number: '{raw}'. "
        f"Expected a 10-digit Indian number or an international number with country code."
    )


def is_valid_e164(phone: str) -> bool:
    """Check if a phone number is in valid E.164 format.

    E.164 numbers start with + followed by 7-15 digits.
    """
    return bool(re.match(r"^\+[1-9]\d{6,14}$", phone))
