"""Application-level symmetric encryption for sensitive fields.

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the `cryptography` library.
The encryption key is loaded from the ENCRYPTION_KEY env var.

SEC-001: WhatsApp access tokens must be encrypted at rest.
SEC-002: Health data fields (medical_conditions, allergies, notes) are also
encrypted at the application layer.

NEW-001 FIX: When both ENCRYPTION_KEY and JWT_SECRET are empty (fresh dev setup),
encryption is skipped with a loud warning instead of using a predictable key.
"""

import base64
import hashlib
import json

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Text
from sqlalchemy import TypeDecorator

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

_fernet: Fernet | None = None
_encryption_disabled = False


def _get_fernet() -> Fernet | None:
    """Lazily initialize Fernet cipher from settings.

    Key resolution order:
    1. ENCRYPTION_KEY env var (recommended for production)
    2. Derived from JWT_SECRET (acceptable for dev with a real secret)
    3. None — encryption disabled with loud warning (empty dev setup only)

    Raises ValueError in production (DEBUG=False) if no usable key is found.
    """
    global _fernet, _encryption_disabled
    if _fernet is not None:
        return _fernet
    if _encryption_disabled:
        return None

    key = settings.ENCRYPTION_KEY

    if not key:
        # Fallback: derive from JWT_SECRET, but only if it's a real secret
        if not settings.JWT_SECRET:
            # NEW-001: Both keys empty — cannot derive a secure key
            if not settings.DEBUG:
                raise ValueError(
                    "ENCRYPTION_KEY must be set in production. "
                    "Cannot encrypt sensitive data without a key."
                )
            logger.warning(
                "⚠️  ENCRYPTION DISABLED: Both ENCRYPTION_KEY and JWT_SECRET are empty. "
                "WhatsApp tokens will be stored in PLAINTEXT. "
                "Set JWT_SECRET or ENCRYPTION_KEY before storing real credentials."
            )
            _encryption_disabled = True
            return None

        # JWT_SECRET is set — derive a Fernet-compatible key from it
        raw = hashlib.sha256(settings.JWT_SECRET.encode()).digest()
        key = base64.urlsafe_b64encode(raw).decode()
        if not settings.DEBUG:
            logger.warning(
                "ENCRYPTION_KEY not set — deriving from JWT_SECRET. "
                "Set a dedicated ENCRYPTION_KEY in production."
            )

    _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt(plaintext: str) -> str:
    """Encrypt a string and return base64-encoded ciphertext.

    Returns plaintext unchanged if encryption is disabled (dev mode, no keys).
    """
    if not plaintext:
        return plaintext
    f = _get_fernet()
    if f is None:
        return plaintext  # Encryption disabled — store as-is
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext back to a string.

    Returns ciphertext unchanged if encryption is disabled (dev mode, no keys).
    """
    if not ciphertext:
        return ciphertext
    f = _get_fernet()
    if f is None:
        return ciphertext  # Encryption disabled — return as-is
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt value — possible key rotation or corruption")
        raise ValueError("Decryption failed. Check ENCRYPTION_KEY configuration.")


# ---------------------------------------------------------------------------
# SQLAlchemy TypeDecorators for transparent column-level encryption
# SEC-002: These wrap Text/ARRAY columns so the service layer doesn't change.
# ---------------------------------------------------------------------------

class EncryptedText(TypeDecorator):
    """Transparently encrypts/decrypts a Text column.

    Stores ciphertext in the DB. Returns plaintext to Python.
    When encryption is disabled (dev, no keys), stores/returns plaintext.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Python → DB: encrypt before storing."""
        if value is None:
            return value
        return encrypt(value)

    def process_result_value(self, value, dialect):
        """DB → Python: decrypt on read.

        Legacy unencrypted data (pre-migration or encryption-disabled writes)
        is detected by checking whether the value looks like Fernet ciphertext.
        Fernet tokens always start with 'gAAAAA' (base64-encoded version byte + timestamp).
        If the value looks like Fernet but decryption fails, that is a real key
        mismatch — it must fail loudly, not silently return garbage.
        """
        if value is None:
            return value
        if value.startswith("gAAAAA"):
            # Looks like Fernet ciphertext — must decrypt or fail hard
            return decrypt(value)
        # Not Fernet-shaped — legacy plaintext, return as-is
        return value


class EncryptedArrayText(TypeDecorator):
    """Transparently encrypts/decrypts a list stored as JSON in a Text column.

    Replaces ARRAY(Text) columns for sensitive health data.
    Stores: encrypt(json.dumps(["diabetes", "PCOS"])) → ciphertext in DB.
    Returns: ["diabetes", "PCOS"] to Python.

    When encryption is disabled, stores plain JSON text.
    Compatible with SQLite (no ARRAY type needed).
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Python list → encrypted JSON string."""
        if value is None:
            return value
        raw = json.dumps(value) if isinstance(value, list) else str(value)
        return encrypt(raw)

    def process_result_value(self, value, dialect):
        """Encrypted JSON string → Python list.

        Legacy unencrypted data from migration 002 is detected by checking
        whether the value looks like Fernet ciphertext (starts with 'gAAAAA').
        If it does look like Fernet but decryption fails, that is a real
        key mismatch and must fail loudly.
        """
        if value is None:
            return value
        if value.startswith("gAAAAA"):
            # Looks like Fernet ciphertext — must decrypt or fail hard
            decrypted = decrypt(value)
        else:
            # Not Fernet-shaped — legacy plaintext JSON from migration 002
            decrypted = value
        try:
            parsed = json.loads(decrypted)
            return parsed if isinstance(parsed, list) else [parsed]
        except (json.JSONDecodeError, ValueError):
            # Fallback: might be a raw comma-separated string (pre-migration)
            return [s.strip() for s in decrypted.split(",") if s.strip()]

