import httpx
from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

class WhatsAppService:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v20.0"
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        
    async def send_text_message(self, to_number: str, body: str, db=None, client_id=None, dietitian_id=None) -> dict | None:
        """Send a plain text message via Meta Graph API."""
        if not self.phone_number_id or not self.access_token:
            logger.warning("WhatsApp credentials not set. Skipping message send.")
            return None
            
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": body}
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                res_data = response.json()
                
                if db:
                    from app.models.whatsapp import WhatsAppMessage
                    msg_id = res_data.get("messages", [{}])[0].get("id", f"out_{int(httpx.AsyncClient()._timeout.read or 0)}")
                    out_msg = WhatsAppMessage(
                        client_id=client_id,
                        dietitian_id=dietitian_id,
                        direction="outbound",
                        wa_message_id=msg_id,
                        from_number=self.phone_number_id,
                        to_number=to_number,
                        message_type="text",
                        message_body=body,
                        status="sent"
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

    async def send_template_message(self, to_number: str, template_name: str, language_code: str = "en", components: list | None = None) -> dict | None:
        """Send a template message via Meta Graph API."""
        if not self.phone_number_id or not self.access_token:
            logger.warning("WhatsApp credentials not set. Skipping message send.")
            return None
            
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }
        if components:
            payload["template"]["components"] = components
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"WhatsApp API error: {e.response.text}")
                return None
            except Exception as e:
                logger.error(f"Error sending WhatsApp template message: {str(e)}")
                return None

whatsapp_service = WhatsAppService()
