# backend/wpp.py
"""Cliente WPPConnect para WhatsApp device-based (POC/homolog)."""
import os
import httpx

WPP_BASE_URL = os.getenv("WPP_BASE_URL", "http://wppconnect:21465")


async def wpp_start_session(session: str):
    """Inicia sessão no WPPConnect (gera QR Code)."""
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{WPP_BASE_URL}/api/{session}/start-session")
        r.raise_for_status()
        return r.json()


async def wpp_get_qr(session: str):
    """Obtém QR Code da sessão para escanear com WhatsApp."""
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{WPP_BASE_URL}/api/{session}/qrcode")
        r.raise_for_status()
        return r.json()


async def wpp_send_text(session: str, phone: str, text: str):
    """
    Envia mensagem de texto via WPPConnect.
    
    Args:
        session: Nome da sessão ativa
        phone: Número com código do país (ex: 5511999999999)
        text: Texto da mensagem
    """
    payload = {"phone": phone, "message": text}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{WPP_BASE_URL}/api/{session}/send-text", json=payload)
        r.raise_for_status()
        return r.json()
