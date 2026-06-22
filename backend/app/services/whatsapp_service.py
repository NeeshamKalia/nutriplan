"""WhatsApp Business Cloud API service.

SD-003: Uses a shared httpx.AsyncClient for connection pooling.
SEC-001: Decrypts per-dietitian WhatsApp access tokens on read.
"""

import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logger import get_logger
from app.utils.encryption import decrypt

logger = get_logger(__name__)


class WhatsAppService:
    """Thin wrapper around the Meta Graph API for WhatsApp messaging.

    SD-003: Maintains a persistent httpx.AsyncClient for TCP connection reuse
    instead of creating a new connection per message.
    """

    def __init__(self):
        self.base_url = "https://graph.facebook.com/v20.0"
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Gracefully close the underlying HTTP client."""
        await self._client.aclose()

    async def _resolve_credentials(
        self, db: AsyncSession | None, dietitian_id=None
    ) -> tuple[str | None, str | None]:
        """Resolve WhatsApp API credentials — per-dietitian first, global env fallback.

        SEC-001: Per-dietitian tokens are decrypted from the database.
        """
        if db is not None and dietitian_id is not None:
            from app.models.dietitian import Dietitian

            result = await db.execute(
                select(Dietitian).where(Dietitian.id == dietitian_id)
            )
            dietitian = result.scalar_one_or_none()
            if (
                dietitian
                and dietitian.whatsapp_phone_number_id
                and dietitian.whatsapp_access_token
            ):
                try:
                    token = decrypt(dietitian.whatsapp_access_token)
                except (ValueError, Exception):
                    # Fallback: token may be stored unencrypted (pre-migration data)
                    token = dietitian.whatsapp_access_token
                    logger.warning(
                        "Could not decrypt WhatsApp token for dietitian %s — using raw value",
                        dietitian_id,
                    )
                return (
                    dietitian.whatsapp_phone_number_id,
                    token,
                )

        return settings.WHATSAPP_PHONE_NUMBER_ID, settings.WHATSAPP_ACCESS_TOKEN

    async def send_text_message(
        self,
        to_number: str,
        body: str,
        db: AsyncSession | None = None,
        client_id=None,
        dietitian_id=None,
    ) -> dict | None:
        """Send a plain text message via Meta Graph API."""
        phone_number_id, access_token = await self._resolve_credentials(db, dietitian_id)

        if not phone_number_id or not access_token:
            logger.warning("WhatsApp credentials not set. Skipping message send.")
            return None

        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": body},
        }

        try:
            response = await self._client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            res_data = response.json()

            if db is not None:
                from app.models.whatsapp_message import WhatsAppMessage

                msg_id = res_data.get("messages", [{}])[0].get(
                    "id", f"out_{uuid.uuid4().hex[:12]}"
                )
                out_msg = WhatsAppMessage(
                    client_id=client_id,
                    dietitian_id=dietitian_id,
                    direction="outbound",
                    wa_message_id=msg_id,
                    from_number=phone_number_id,
                    to_number=to_number,
                    message_type="text",
                    message_body=body,
                    status="sent",
                )
                db.add(out_msg)
                await db.commit()

            return res_data
        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp API error: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return None

    async def send_template_message(
        self,
        to_number: str,
        template_name: str,
        language_code: str = "en",
        components: list | None = None,
        db: AsyncSession | None = None,
        dietitian_id=None,
    ) -> dict | None:
        """Send a template message via Meta Graph API."""
        phone_number_id, access_token = await self._resolve_credentials(db, dietitian_id)

        if not phone_number_id or not access_token:
            logger.warning("WhatsApp credentials not set. Skipping message send.")
            return None

        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }
        if components:
            payload["template"]["components"] = components

        try:
            response = await self._client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp API error: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error sending WhatsApp template message: {str(e)}")
            return None


whatsapp_service = WhatsAppService()
