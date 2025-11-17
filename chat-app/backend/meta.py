# backend/meta.py
"""Cliente Meta Graph API para WhatsApp Cloud, Instagram e Facebook Messenger."""
import os
import httpx
import hmac
import hashlib
from typing import Literal

META_APP_SECRET = os.getenv("META_APP_SECRET", "")
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "")

# Facebook Messenger
META_PAGE_ID = os.getenv("META_PAGE_ID", "")
META_PAGE_ACCESS_TOKEN = os.getenv("META_PAGE_ACCESS_TOKEN", "")

# Instagram Messaging
IG_BIZ_ACCOUNT_ID = os.getenv("IG_BIZ_ACCOUNT_ID", "")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")

# WhatsApp Cloud API
WA_PHONE_NUMBER_ID = os.getenv("WA_PHONE_NUMBER_ID", "")
WA_CLOUD_ACCESS_TOKEN = os.getenv("WA_CLOUD_ACCESS_TOKEN", "")

Channel = Literal["whatsapp", "instagram", "facebook"]


def verify_meta_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """
    Verifica assinatura HMAC do webhook Meta.
    
    Args:
        raw_body: Corpo bruto da requisição
        signature_header: Header X-Hub-Signature-256
        
    Returns:
        True se assinatura válida
    """
    if not signature_header or not META_APP_SECRET:
        return False
    try:
        prefix, received = signature_header.split("=", 1)
        mac = hmac.new(META_APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(received, mac)
    except Exception:
        return False


async def meta_send_message(channel: Channel, recipient: str, text: str) -> dict:
    """
    Envia mensagem via Meta Graph API (WhatsApp Cloud, Instagram ou Facebook).
    
    Args:
        channel: Canal de destino ('whatsapp', 'instagram', 'facebook')
        recipient: ID do destinatário (PSID para IG/FB, número E.164 para WA)
        text: Texto da mensagem
        
    Returns:
        Resposta da API Meta
        
    Raises:
        ValueError: Se credenciais estiverem faltando ou inválidas
    """
    async with httpx.AsyncClient(timeout=30) as c:
        if channel == "whatsapp":
            # WhatsApp Cloud API
            if not WA_PHONE_NUMBER_ID or not WA_CLOUD_ACCESS_TOKEN:
                raise ValueError("Credenciais do WhatsApp Cloud não configuradas. Configure WA_PHONE_NUMBER_ID e WA_CLOUD_ACCESS_TOKEN no .env")
            
            if not WA_CLOUD_ACCESS_TOKEN.strip():
                raise ValueError("WA_CLOUD_ACCESS_TOKEN está vazio no .env")
            
            url = f"https://graph.facebook.com/v20.0/{WA_PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {WA_CLOUD_ACCESS_TOKEN}"}
            body = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"body": text}
            }
            r = await c.post(url, headers=headers, json=body)
            r.raise_for_status()
            return r.json()

        elif channel == "instagram":
            # Instagram Messaging API
            if not IG_BIZ_ACCOUNT_ID or not IG_ACCESS_TOKEN:
                raise ValueError("Credenciais do Instagram não configuradas. Configure IG_BIZ_ACCOUNT_ID e IG_ACCESS_TOKEN no .env")
            
            url = f"https://graph.facebook.com/v20.0/{IG_BIZ_ACCOUNT_ID}/messages"
            params = {"access_token": IG_ACCESS_TOKEN}
            body = {
                "recipient": {"id": recipient},
                "message": {"text": text}
            }
            r = await c.post(url, params=params, json=body)
            r.raise_for_status()
            return r.json()

        elif channel == "facebook":
            # Facebook Messenger API
            if not META_PAGE_ID or not META_PAGE_ACCESS_TOKEN:
                raise ValueError("Credenciais do Facebook não configuradas. Configure META_PAGE_ID e META_PAGE_ACCESS_TOKEN no .env")
            
            url = f"https://graph.facebook.com/v20.0/{META_PAGE_ID}/messages"
            params = {"access_token": META_PAGE_ACCESS_TOKEN}
            body = {
                "recipient": {"id": recipient},
                "message": {"text": text}
            }
            r = await c.post(url, params=params, json=body)
            r.raise_for_status()
            return r.json()

        else:
            raise ValueError(f"Canal não suportado: {channel}")
