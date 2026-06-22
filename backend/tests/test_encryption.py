"""Tests for encryption type decorators — Fernet detection and legacy fallback.

Verifies that:
- Fernet-encrypted values decrypt correctly
- Legacy plaintext (non-Fernet) is returned as-is
- Wrong-key Fernet ciphertext fails loudly (not silently returned as plaintext)
- EncryptedArrayText correctly parses legacy JSON arrays
"""

import json
import pytest
from unittest.mock import patch

from cryptography.fernet import Fernet


class TestFernetDetection:
    """Tests for the gAAAAA Fernet prefix heuristic."""

    def test_plaintext_not_fernet_shaped(self):
        """Plain strings don't start with gAAAAA — treated as legacy."""
        from app.utils.encryption import EncryptedText
        et = EncryptedText()
        assert et.process_result_value("hello world", dialect=None) == "hello world"

    def test_json_array_not_fernet_shaped(self):
        """JSON arrays from migration 002 don't start with gAAAAA — treated as legacy."""
        from app.utils.encryption import EncryptedArrayText
        eat = EncryptedArrayText()
        result = eat.process_result_value('["diabetes", "PCOS"]', dialect=None)
        assert result == ["diabetes", "PCOS"]

    def test_none_returns_none(self):
        """None values pass through unchanged."""
        from app.utils.encryption import EncryptedText, EncryptedArrayText
        et = EncryptedText()
        eat = EncryptedArrayText()
        assert et.process_result_value(None, dialect=None) is None
        assert eat.process_result_value(None, dialect=None) is None

    def test_valid_fernet_decrypts(self):
        """Real Fernet ciphertext decrypts when the key matches."""
        from app.utils.encryption import EncryptedText

        key = Fernet.generate_key()
        f = Fernet(key)
        ciphertext = f.encrypt(b"sensitive data").decode()
        # Confirm it starts with gAAAAA
        assert ciphertext.startswith("gAAAAA")

        et = EncryptedText()
        # Patch _get_fernet to return our test Fernet instance
        with patch("app.utils.encryption._get_fernet", return_value=f):
            result = et.process_result_value(ciphertext, dialect=None)
        assert result == "sensitive data"

    def test_wrong_key_fernet_fails_loudly(self):
        """Fernet ciphertext with wrong key raises ValueError — not silently returned."""
        from app.utils.encryption import EncryptedText

        # Encrypt with key A
        key_a = Fernet.generate_key()
        f_a = Fernet(key_a)
        ciphertext = f_a.encrypt(b"secret").decode()
        assert ciphertext.startswith("gAAAAA")

        # Try to decrypt with key B
        key_b = Fernet.generate_key()
        f_b = Fernet(key_b)

        et = EncryptedText()
        with patch("app.utils.encryption._get_fernet", return_value=f_b):
            with pytest.raises(ValueError, match="Decryption failed"):
                et.process_result_value(ciphertext, dialect=None)

    def test_wrong_key_encrypted_array_fails_loudly(self):
        """EncryptedArrayText with wrong key also raises — not silently parsed."""
        from app.utils.encryption import EncryptedArrayText

        # Encrypt with key A
        key_a = Fernet.generate_key()
        f_a = Fernet(key_a)
        ciphertext = f_a.encrypt(json.dumps(["allergy1"]).encode()).decode()
        assert ciphertext.startswith("gAAAAA")

        # Try to decrypt with key B
        key_b = Fernet.generate_key()
        f_b = Fernet(key_b)

        eat = EncryptedArrayText()
        with patch("app.utils.encryption._get_fernet", return_value=f_b):
            with pytest.raises(ValueError, match="Decryption failed"):
                eat.process_result_value(ciphertext, dialect=None)

    def test_encrypted_array_roundtrip(self):
        """EncryptedArrayText encrypt→store→read roundtrip works."""
        from app.utils.encryption import EncryptedArrayText

        key = Fernet.generate_key()
        f = Fernet(key)

        eat = EncryptedArrayText()
        with patch("app.utils.encryption._get_fernet", return_value=f):
            stored = eat.process_bind_param(["diabetes", "PCOS"], dialect=None)
            # Stored value should be Fernet-shaped
            assert stored.startswith("gAAAAA")
            # Read it back
            result = eat.process_result_value(stored, dialect=None)
        assert result == ["diabetes", "PCOS"]

    def test_legacy_comma_separated_string(self):
        """Pre-migration comma-separated strings are handled by EncryptedArrayText."""
        from app.utils.encryption import EncryptedArrayText
        eat = EncryptedArrayText()
        result = eat.process_result_value("diabetes, PCOS, thyroid", dialect=None)
        assert result == ["diabetes", "PCOS", "thyroid"]

    def test_encryption_disabled_passthrough(self):
        """When encryption is disabled, values pass through unchanged."""
        from app.utils.encryption import EncryptedText, EncryptedArrayText

        et = EncryptedText()
        eat = EncryptedArrayText()

        # With encryption disabled (_get_fernet returns None), encrypt() returns plaintext
        with patch("app.utils.encryption._get_fernet", return_value=None):
            stored_text = et.process_bind_param("notes here", dialect=None)
            assert stored_text == "notes here"

            stored_array = eat.process_bind_param(["item1", "item2"], dialect=None)
            # When disabled, encrypt() returns the JSON string as-is
            assert json.loads(stored_array) == ["item1", "item2"]
