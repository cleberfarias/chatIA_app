# backend/wpp.py
"""
Cliente WhatsApp via Selenium + Firefox.
Lê QR Code do MongoDB (capturado por screenshot do WhatsApp Web).
Baseado na arquitetura documentada.
"""
import os
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# URL do serviço Selenium
SELENIUM_BASE_URL = os.getenv("SELENIUM_BASE_URL", "http://whatsapp-selenium:21466")

# MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
MONGO_DB = os.getenv("MONGO_DB", "chatapp")

# Cliente MongoDB (inicializado globalmente)
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[MONGO_DB]


async def wpp_get_status(session: str = "default"):
    """
    Obtém status da conexão WhatsApp.
    Lê diretamente do MongoDB.
    """
    try:
        # Busca no MongoDB
        session_data = await db.whatsapp_sessions.find_one(
            {"session_name": session},
            {"status": 1, "last_update": 1, "_id": 0}
        )
        
        if not session_data:
            return {
                "connected": False,
                "status": "STARTING",
                "message": "Inicializando..."
            }
        
        status = session_data.get("status", "STARTING")
        
        return {
            "connected": status == "LOGGEDIN",
            "status": status,
            "last_update": session_data.get("last_update", datetime.utcnow()).isoformat()
        }
    
    except Exception as e:
        print(f"❌ Erro ao buscar status: {e}")
        return {
            "connected": False,
            "status": "ERROR",
            "message": str(e)
        }


async def wpp_get_qr(session: str = "default", check_containers: bool = False):
    """
    Obtém QR Code para conexão.
    Lê diretamente do MongoDB onde o Selenium salvou.
    
    Args:
        session: Nome da sessão
        check_containers: Se True, verifica se container está rodando (primeira chamada)
    
    Returns:
        {
            "qr_code": "base64...",
            "status": "CAPTURAR QR-CODE",
            "last_update": "2025-11-17T10:30:00",
            "description": "Mensagem para o usuário"
        }
    """
    try:
        # Busca no MongoDB
        session_data = await db.whatsapp_sessions.find_one(
            {"session_name": session}
        )
        
        if not session_data:
            return {
                "qr_code": "",
                "status": "STARTING",
                "last_update": datetime.utcnow().isoformat(),
                "description": "Inicializando WhatsApp Web. Por favor aguarde..."
            }
        
        status = session_data.get("status", "STARTING")
        qr_code = session_data.get("qr_code", "")
        last_update = session_data.get("last_update", datetime.utcnow())
        
        # Monta resposta baseada no status
        if status == "LOGGEDIN":
            return {
                "qr_code": "",
                "status": status,
                "last_update": last_update.isoformat(),
                "description": "WhatsApp conectado com sucesso! ✓"
            }
        
        elif status == "CAPTURAR QR-CODE" and qr_code:
            return {
                "qr_code": qr_code,
                "status": status,
                "last_update": last_update.isoformat(),
                "description": "Capture o QR-Code abaixo para conectar seu aparelho."
            }
        
        elif status in ["STARTING", "WAITING_LOGIN", "LOGGEDINWAIT"]:
            return {
                "qr_code": "",
                "status": status,
                "last_update": last_update.isoformat(),
                "description": "Carregando... Por favor aguarde."
            }
        
        else:
            return {
                "qr_code": "",
                "status": status,
                "last_update": last_update.isoformat(),
                "description": "QR Code não disponível. Por favor, tente novamente."
            }
    
    except Exception as e:
        print(f"❌ Erro ao buscar QR Code: {e}")
        return {
            "qr_code": "",
            "status": "ERROR",
            "last_update": datetime.utcnow().isoformat(),
            "description": f"Erro ao buscar QR Code: {str(e)}"
        }


async def wpp_restart_session(session: str = "default"):
    """
    Reinicia a sessão WhatsApp (limpa cache e recarrega).
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{SELENIUM_BASE_URL}/restart")
            return response.json()
    except Exception as e:
        print(f"❌ Erro ao reiniciar sessão: {e}")
        return {"error": str(e)}


async def wpp_send_text(session: str, phone: str, text: str):
    """
    Envia mensagem de texto via WhatsApp.
    
    Args:
        session: Nome da sessão
        phone: Número com código do país (ex: 5511999999999)
        text: Texto da mensagem
    
    Note:
        Esta funcionalidade requer implementação adicional no Selenium
        para interagir com a interface web do WhatsApp.
    """
    # TODO: Implementar envio de mensagem via Selenium
    raise NotImplementedError("Envio de mensagem será implementado em breve")
