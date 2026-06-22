"""Convert health fields from ARRAY to TEXT for encryption.

Migration 001 created medical_conditions and allergies as ARRAY(Text)
columns. The model now uses EncryptedArrayText() which stores encrypted
JSON as a single Text value. This migration converts the column types,
migrates existing data to JSON, and encrypts it using the application's
Fernet encryption (if an encryption key is configured).

Revision ID: 002
Revises: 001
Create Date: 2026-06-20
"""
import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def _encrypt_value(plaintext: str) -> str:
    """Encrypt a value using the application's Fernet key, if available.

    Falls back to plaintext when encryption is disabled (no key configured).
    This is a migration-time helper — it imports the app encryption module
    so the migration uses the same key as the running application.
    """
    try:
        from app.utils.encryption import encrypt
        return encrypt(plaintext)
    except ImportError:
        # If encryption module can't be loaded (e.g. offline migration),
        # store as plaintext — the app will encrypt on next write.
        return plaintext


def upgrade() -> None:
    # Step 1: Add temporary text columns
    op.add_column("clients", sa.Column("medical_conditions_text", sa.Text(), nullable=True))
    op.add_column("clients", sa.Column("allergies_text", sa.Text(), nullable=True))

    # Step 2: Migrate existing array data to JSON text, then encrypt
    conn = op.get_bind()

    # First, convert arrays to JSON text in the temp columns
    conn.execute(
        sa.text(
            "UPDATE clients SET "
            "medical_conditions_text = array_to_json(medical_conditions)::text, "
            "allergies_text = array_to_json(allergies)::text "
            "WHERE medical_conditions IS NOT NULL OR allergies IS NOT NULL"
        )
    )

    # Then, encrypt the JSON values row by row
    rows = conn.execute(
        sa.text(
            "SELECT id, medical_conditions_text, allergies_text "
            "FROM clients "
            "WHERE medical_conditions_text IS NOT NULL OR allergies_text IS NOT NULL"
        )
    ).fetchall()

    for row in rows:
        updates = {}
        if row.medical_conditions_text:
            updates["mc"] = _encrypt_value(row.medical_conditions_text)
        if row.allergies_text:
            updates["al"] = _encrypt_value(row.allergies_text)

        if updates:
            conn.execute(
                sa.text(
                    "UPDATE clients SET "
                    "medical_conditions_text = :mc, "
                    "allergies_text = :al "
                    "WHERE id = :id"
                ),
                {
                    "mc": updates.get("mc", row.medical_conditions_text),
                    "al": updates.get("al", row.allergies_text),
                    "id": row.id,
                },
            )

    # Step 3: Drop old ARRAY columns and rename new ones
    op.drop_column("clients", "medical_conditions")
    op.drop_column("clients", "allergies")
    op.alter_column("clients", "medical_conditions_text", new_column_name="medical_conditions")
    op.alter_column("clients", "allergies_text", new_column_name="allergies")


def downgrade() -> None:
    # Step 1: Add temporary array columns
    op.add_column("clients", sa.Column("medical_conditions_arr", postgresql.ARRAY(sa.Text()), nullable=True))
    op.add_column("clients", sa.Column("allergies_arr", postgresql.ARRAY(sa.Text()), nullable=True))

    # Step 2: Decrypt and migrate JSON text back to arrays
    conn = op.get_bind()

    # First decrypt row by row
    rows = conn.execute(
        sa.text(
            "SELECT id, medical_conditions, allergies "
            "FROM clients "
            "WHERE medical_conditions IS NOT NULL OR allergies IS NOT NULL"
        )
    ).fetchall()

    for row in rows:
        mc_json = row.medical_conditions
        al_json = row.allergies

        # Try to decrypt if encrypted
        try:
            from app.utils.encryption import decrypt
            if mc_json and mc_json.startswith("gAAAAA"):
                mc_json = decrypt(mc_json)
            if al_json and al_json.startswith("gAAAAA"):
                al_json = decrypt(al_json)
        except Exception:
            pass  # Use as-is if decryption unavailable

        # Parse JSON and convert to PostgreSQL array literal
        if mc_json:
            mc_list = json.loads(mc_json) if mc_json else []
            conn.execute(
                sa.text("UPDATE clients SET medical_conditions_arr = :arr WHERE id = :id"),
                {"arr": mc_list, "id": row.id},
            )
        if al_json:
            al_list = json.loads(al_json) if al_json else []
            conn.execute(
                sa.text("UPDATE clients SET allergies_arr = :arr WHERE id = :id"),
                {"arr": al_list, "id": row.id},
            )

    # Step 3: Drop text columns and rename array columns back
    op.drop_column("clients", "medical_conditions")
    op.drop_column("clients", "allergies")
    op.alter_column("clients", "medical_conditions_arr", new_column_name="medical_conditions")
    op.alter_column("clients", "allergies_arr", new_column_name="allergies")
