import pytest
import hmac
import hashlib
import json
from httpx import AsyncClient
from app.config import settings

@pytest.mark.asyncio
async def test_verify_webhook_success(client: AsyncClient):
    settings.WHATSAPP_VERIFY_TOKEN = "my_secret_token"
    response = await client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "my_secret_token",
            "hub.challenge": "123456"
        }
    )
    assert response.status_code == 200
    assert response.text == "123456"

@pytest.mark.asyncio
async def test_verify_webhook_fail(client: AsyncClient):
    settings.WHATSAPP_VERIFY_TOKEN = "my_secret_token"
    response = await client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "123456"
        }
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_receive_webhook_valid_signature(client: AsyncClient):
    settings.WHATSAPP_APP_SECRET = "test_secret"
    payload = {"object": "whatsapp_business_account", "entry": []}
    payload_bytes = json.dumps(payload).encode('utf-8')
    
    signature = hmac.new(
        key=settings.WHATSAPP_APP_SECRET.encode('utf-8'),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    headers = {
        "X-Hub-Signature-256": f"sha256={signature}",
        "Content-Type": "application/json"
    }
    
    response = await client.post("/webhook/whatsapp", content=payload_bytes, headers=headers)
        
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_receive_webhook_invalid_signature(client: AsyncClient):
    settings.WHATSAPP_APP_SECRET = "test_secret"
    payload = {"object": "whatsapp_business_account", "entry": []}
    payload_bytes = json.dumps(payload).encode('utf-8')
    headers = {
        "X-Hub-Signature-256": "sha256=invalid_signature",
        "Content-Type": "application/json"
    }
    
    response = await client.post("/webhook/whatsapp", content=payload_bytes, headers=headers)
        
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_receive_webhook_duplicate_idempotency(client: AsyncClient):
    settings.WHATSAPP_APP_SECRET = "test_secret"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "id": "wa_msg_123",
                        "from": "919999999999",
                        "type": "text",
                        "text": {"body": "hello"}
                    }]
                }
            }]
        }]
    }
    payload_bytes = json.dumps(payload).encode('utf-8')
    signature = hmac.new(key=settings.WHATSAPP_APP_SECRET.encode('utf-8'), msg=payload_bytes, digestmod=hashlib.sha256).hexdigest()
    headers = {"X-Hub-Signature-256": f"sha256={signature}", "Content-Type": "application/json"}
    
    # Send first time
    response1 = await client.post("/webhook/whatsapp", content=payload_bytes, headers=headers)
    assert response1.status_code == 200
    
    # Send second time
    response2 = await client.post("/webhook/whatsapp", content=payload_bytes, headers=headers)
    assert response2.status_code == 200
