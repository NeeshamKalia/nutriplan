import hashlib
import hmac
from fastapi import APIRouter, Request, Response, BackgroundTasks, HTTPException, Query
from app.config import settings
from app.core.logger import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models.whatsapp_message import WhatsAppMessage
from app.models.client import Client
from app.models.dietitian import Dietitian
from sqlalchemy import select

logger = get_logger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge")
):
    """Verify webhook with Meta."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

async def process_whatsapp_message(payload: dict):
    """Background task to process the incoming webhook payload.

    Tenant isolation: identifies the dietitian from the receiving phone_number_id
    in the webhook metadata, then scopes the client lookup by dietitian_id.
    """
    async with async_session() as db:
        try:
            entries = payload.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    metadata = value.get("metadata", {})
                    messages = value.get("messages", [])

                    # Step 1: Identify which dietitian owns this WhatsApp number
                    phone_number_id = metadata.get("phone_number_id")
                    display_phone_number = metadata.get("display_phone_number")

                    dietitian = None
                    if phone_number_id:
                        result = await db.execute(
                            select(Dietitian).where(
                                Dietitian.whatsapp_phone_number_id == phone_number_id
                            )
                        )
                        dietitian = result.scalar_one_or_none()

                    if not dietitian:
                        logger.warning(
                            f"No dietitian found for phone_number_id={phone_number_id}. "
                            f"Message from unknown WhatsApp Business Account."
                        )

                    for msg in messages:
                        from_number = msg.get("from")
                        wa_message_id = msg.get("id")
                        msg_type = msg.get("type")
                        
                        body = ""
                        if msg_type == "text":
                            body = msg.get("text", {}).get("body", "")
                            
                        # Idempotency check: avoid processing duplicate webhooks
                        existing_msg = await db.execute(
                            select(WhatsAppMessage).where(WhatsAppMessage.wa_message_id == wa_message_id)
                        )
                        if existing_msg.scalar_one_or_none():
                            logger.info(f"Duplicate message {wa_message_id} ignored")
                            continue

                        # Format the number for lookup
                        db_number = f"+{from_number}" if from_number and not from_number.startswith("+") else from_number
                        
                        # Step 2: Tenant-scoped client lookup
                        client = None
                        if db_number and dietitian:
                            result = await db.execute(
                                select(Client).where(
                                    Client.dietitian_id == dietitian.id,
                                    Client.whatsapp_number == db_number,
                                )
                            )
                            client = result.scalar_one_or_none()
                        
                        intent = "unknown"
                        if body:
                            from app.whatsapp.intent_classifier import classify_intent
                            intent = classify_intent(body)
                        
                        wa_msg = WhatsAppMessage(
                            client_id=client.id if client else None,
                            dietitian_id=dietitian.id if dietitian else None,
                            direction="inbound",
                            wa_message_id=wa_message_id,
                            from_number=from_number,
                            to_number=display_phone_number,
                            message_type=msg_type,
                            message_body=body,
                            status="received",
                            intent=intent
                        )
                        db.add(wa_msg)
                        await db.commit()
                        
                        if not client:
                            continue
                            
                        # Handle commands
                        if intent == 'command_help':
                            from app.whatsapp.handlers.help import handle_help
                            await handle_help(from_number)
                        elif intent == 'command_today':
                            from app.whatsapp.handlers.today import handle_today
                            await handle_today(db, client, from_number)
                        elif intent == 'command_grocery':
                            from app.whatsapp.handlers.grocery import handle_grocery
                            await handle_grocery(db, client, from_number)
                        elif intent == 'unknown' and msg_type == 'text':
                            from app.services.whatsapp_service import whatsapp_service
                            await whatsapp_service.send_text_message(from_number, "I didn't understand. Send HELP for commands!")
                        
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")

def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify the X-Hub-Signature-256 header."""
    if not settings.WHATSAPP_APP_SECRET or not signature_header:
        return False
    
    expected_signature = hmac.new(
        key=settings.WHATSAPP_APP_SECRET.encode(),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if signature_header.startswith("sha256="):
        signature = signature_header[7:]
        return hmac.compare_digest(expected_signature, signature)
    return False

@router.post("/whatsapp")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive messages from WhatsApp."""
    payload_body = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256", "")
    
    if not verify_signature(payload_body, signature_header):
        logger.warning("Invalid or missing webhook signature")
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = await request.json()
    background_tasks.add_task(process_whatsapp_message, payload)
    return {"status": "ok"}
