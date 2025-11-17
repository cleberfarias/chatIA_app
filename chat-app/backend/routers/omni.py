# backend/routers/omni.py
"""Router omnichannel para envio unificado via WhatsApp, Instagram e Facebook."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from database import messages_collection
import sys
import os

# Adiciona o diretório pai ao path para importar módulos do backend
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from meta import meta_send_message
from wpp import wpp_start_session, wpp_get_qr, wpp_send_text

router = APIRouter(prefix="/omni", tags=["omnichannel"])


class SendIn(BaseModel):
    """Schema para envio de mensagem omnichannel."""
    channel: str  # 'whatsapp' | 'instagram' | 'facebook' | 'wppconnect'
    recipient: str  # WhatsApp: número E.164; IG/FB: PSID
    text: str
    session: str | None = None  # Obrigatório para wppconnect


@router.post("/send")
async def omni_send(body: SendIn):
    """
    Envia mensagem de forma unificada para qualquer canal.
    
    - **whatsapp**: WhatsApp Cloud API (oficial)
    - **instagram**: Instagram Messaging
    - **facebook**: Facebook Messenger
    - **wppconnect**: WhatsApp device-based (POC)
    """
    try:
        # Importa sio aqui para evitar circular import
        from main import sio
        
        if body.channel == "wppconnect":
            if not body.session:
                raise HTTPException(400, "session é obrigatória para wppconnect")
            result = await wpp_send_text(body.session, body.recipient, body.text)
            author = "Bot(wa-dev)"
        else:
            result = await meta_send_message(body.channel, body.recipient, body.text)
            author = f"Bot({body.channel})"

        # Espelha no chat via WebSocket
        now = datetime.now(timezone.utc)
        doc = {
            "author": author,
            "text": f"→ {body.recipient}: {body.text}",
            "type": "text",
            "status": "sent",
            "createdAt": now
        }
        rid = (await messages_collection.insert_one(doc)).inserted_id
        
        await sio.emit("chat:new-message", {
            "id": str(rid),
            "author": author,
            "text": doc["text"],
            "type": "text",
            "status": "sent",
            "timestamp": int(now.timestamp() * 1000)
        })
        
        return {"ok": True, "result": result}
        
    except Exception as e:
        raise HTTPException(400, str(e))


# --- Sessão WPPConnect (opcional para POC/homolog) ---

class StartSessionIn(BaseModel):
    """Schema para iniciar sessão WPPConnect."""
    session: str


@router.post("/wpp/start")
async def start_wpp_session(body: StartSessionIn):
    """
    Inicia sessão WPPConnect (gera QR Code).
    
    Use /wpp/qr para obter o QR Code gerado.
    """
    try:
        return await wpp_start_session(body.session)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/wpp/qr")
async def get_wpp_qr(session: str):
    """
    Obtém QR Code da sessão WPPConnect.
    
    Escaneie com o WhatsApp para conectar.
    """
    try:
        return await wpp_get_qr(session)
    except Exception as e:
        raise HTTPException(400, str(e))
