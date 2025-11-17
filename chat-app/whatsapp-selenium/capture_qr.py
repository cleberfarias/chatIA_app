#!/usr/bin/env python3
"""
Script de captura de QR Code do WhatsApp Web usando Selenium + Firefox.
Baseado na arquitetura da documentação fornecida.
"""
import os
import time
import base64
from datetime import datetime
from io import BytesIO
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from PIL import Image

from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import asyncio


# ==================== CONFIGURAÇÃO ====================

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
MONGO_DB = os.getenv("MONGO_DB", "chatapp")

WHATSAPP_WEB_URL = "https://web.whatsapp.com"
SESSION_NAME = "default"

# Estados do WhatsApp
STATUS_STARTING = "STARTING"
STATUS_WAITING_LOGIN = "WAITING_LOGIN"
STATUS_QR_CODE_READY = "CAPTURAR QR-CODE"
STATUS_QR_CODE_REQUEST = "QR_CODE_REQUEST"
STATUS_LOGGED_IN_WAIT = "LOGGEDINWAIT"
STATUS_LOGGED_IN = "LOGGEDIN"
STATUS_ERROR = "ERROR"


# ==================== GLOBALS ====================

app = FastAPI(title="WhatsApp QR Code Capture Service")
driver: Optional[webdriver.Firefox] = None
mongo_client: Optional[AsyncIOMotorClient] = None
db = None
is_initialized = False
current_status = STATUS_STARTING
qr_code_base64 = ""


# ==================== SELENIUM ====================

def init_driver():
    """Inicializa o driver do Selenium com Firefox."""
    global driver
    
    if driver:
        try:
            driver.quit()
        except:
            pass
    
    print("🔄 Iniciando Firefox local...")
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Perfil para salvar sessão do WhatsApp
    profile_path = "/app/sessions/firefox_profile"
    os.makedirs(profile_path, exist_ok=True)
    options.profile = webdriver.FirefoxProfile(profile_path)
    
    # Usa geckodriver local instalado no sistema
    driver = webdriver.Firefox(options=options)
    driver.set_window_size(1280, 720)
    
    print("✅ Firefox iniciado localmente!")
    return driver


def capture_qr_code() -> Optional[str]:
    """
    Captura o QR Code da página do WhatsApp Web.
    
    Returns:
        Base64 da imagem do QR Code ou None se não encontrado
    """
    global driver
    
    try:
        # Aguarda o canvas do QR Code aparecer
        qr_canvas = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "canvas[aria-label='Scan this QR code to link a device!']"))
        )
        
        print("📱 QR Code detectado! Capturando screenshot...")
        
        # Tira screenshot do elemento
        png_data = qr_canvas.screenshot_as_png
        
        # Converte para base64
        qr_base64 = base64.b64encode(png_data).decode('utf-8')
        
        print("✅ QR Code capturado com sucesso!")
        return qr_base64
        
    except TimeoutException:
        print("⏱️ Timeout: QR Code não encontrado")
        return None
    except Exception as e:
        print(f"❌ Erro ao capturar QR Code: {e}")
        return None


def check_if_logged_in() -> bool:
    """Verifica se o WhatsApp Web está logado."""
    global driver
    
    try:
        # Procura por elementos que indicam que está logado
        # (chat list, search box, etc)
        driver.find_element(By.CSS_SELECTOR, "div[aria-label='Chat list']")
        return True
    except NoSuchElementException:
        return False


async def update_status_in_db(status: str, qr_code: str = ""):
    """Atualiza status e QR Code no MongoDB."""
    global db, current_status, qr_code_base64
    
    current_status = status
    qr_code_base64 = qr_code
    
    try:
        await db.whatsapp_sessions.update_one(
            {"session_name": SESSION_NAME},
            {
                "$set": {
                    "status": status,
                    "qr_code": qr_code,
                    "last_update": datetime.utcnow(),
                }
            },
            upsert=True
        )
        print(f"📊 Status atualizado: {status}")
    except Exception as e:
        print(f"❌ Erro ao atualizar DB: {e}")


async def whatsapp_monitor_loop():
    """Loop principal que monitora o WhatsApp e captura QR Code."""
    global driver, is_initialized
    
    while True:
        try:
            if not driver:
                driver = init_driver()
            
            # Navega para WhatsApp Web
            print(f"🌐 Acessando {WHATSAPP_WEB_URL}...")
            driver.get(WHATSAPP_WEB_URL)
            
            await update_status_in_db(STATUS_WAITING_LOGIN)
            
            # Aguarda a página carregar
            time.sleep(5)
            
            # Loop de monitoramento
            while True:
                # Verifica se está logado
                if check_if_logged_in():
                    print("✅ WhatsApp está logado!")
                    await update_status_in_db(STATUS_LOGGED_IN, "")
                    is_initialized = True
                    
                    # Aguarda por 30 segundos antes de verificar novamente
                    await asyncio.sleep(30)
                    continue
                
                # Se não está logado, tenta capturar QR Code
                qr = capture_qr_code()
                
                if qr:
                    # Verifica se é QR Code novo (comparando com anterior)
                    if qr != qr_code_base64:
                        print("🔄 QR Code renovado! Atualizando...")
                    
                    await update_status_in_db(STATUS_QR_CODE_READY, qr)
                    is_initialized = True
                    
                    # Aguarda 2 segundos antes de verificar novamente (mais rápido)
                    await asyncio.sleep(2)
                else:
                    await update_status_in_db(STATUS_WAITING_LOGIN, "")
                    await asyncio.sleep(3)
        
        except Exception as e:
            print(f"❌ Erro no loop de monitoramento: {e}")
            await update_status_in_db(STATUS_ERROR, "")
            await asyncio.sleep(10)
            
            # Tenta reiniciar o driver
            try:
                if driver:
                    driver.quit()
                driver = None
            except:
                pass


# ==================== API REST ====================

@app.on_event("startup")
async def startup():
    """Inicializa conexões e inicia o loop de monitoramento."""
    global mongo_client, db
    
    print("🚀 Iniciando WhatsApp QR Code Capture Service...")
    
    # Inicia Xvfb para Firefox headless
    import subprocess
    try:
        subprocess.Popen(['Xvfb', ':99', '-ac', '-screen', '0', '1280x1024x24'], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.environ['DISPLAY'] = ':99'
        await asyncio.sleep(2)  # Aguarda Xvfb iniciar
        print("✅ Xvfb iniciado (display :99)")
    except Exception as e:
        print(f"⚠️ Erro ao iniciar Xvfb: {e}")
    
    # Conecta ao MongoDB
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    db = mongo_client[MONGO_DB]
    
    print(f"✅ Conectado ao MongoDB: {MONGO_URL}")
    
    # Inicia o loop de monitoramento em background
    asyncio.create_task(whatsapp_monitor_loop())
    
    print("✅ Serviço iniciado!")


@app.on_event("shutdown")
async def shutdown():
    """Fecha conexões."""
    global driver, mongo_client
    
    if driver:
        try:
            driver.quit()
        except:
            pass
    
    if mongo_client:
        mongo_client.close()
    
    print("👋 Serviço encerrado")


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "ok",
        "initialized": is_initialized,
        "current_status": current_status
    }


@app.get("/status")
async def get_status():
    """Retorna status atual da conexão."""
    return {
        "connected": current_status == STATUS_LOGGED_IN,
        "status": current_status,
        "initialized": is_initialized,
        "last_update": datetime.utcnow().isoformat()
    }


@app.get("/qr")
async def get_qr():
    """
    Retorna QR Code para conexão.
    Endpoint compatível com o polling do frontend.
    """
    global current_status, qr_code_base64
    
    # Se já está conectado
    if current_status == STATUS_LOGGED_IN:
        return {
            "connected": True,
            "message": "WhatsApp já está conectado",
            "qr": "",
            "status": STATUS_LOGGED_IN
        }
    
    # Se tem QR Code disponível
    if qr_code_base64 and current_status == STATUS_QR_CODE_READY:
        return {
            "connected": False,
            "message": "Escaneie o QR Code com seu WhatsApp",
            "qr": qr_code_base64,
            "status": STATUS_QR_CODE_READY
        }
    
    # Se está inicializando
    if current_status in [STATUS_STARTING, STATUS_WAITING_LOGIN, STATUS_LOGGED_IN_WAIT]:
        return {
            "connected": False,
            "message": "Carregando... Por favor aguarde.",
            "qr": "",
            "status": current_status
        }
    
    # Erro
    return {
        "connected": False,
        "message": "QR Code não disponível. Tente novamente.",
        "qr": "",
        "status": STATUS_ERROR
    }


@app.post("/restart")
async def restart_session():
    """Reinicia a sessão (limpa cache e recarrega)."""
    global driver, current_status, qr_code_base64
    
    print("🔄 Reiniciando sessão...")
    
    try:
        if driver:
            driver.quit()
            driver = None
        
        # Limpa status
        current_status = STATUS_STARTING
        qr_code_base64 = ""
        
        await update_status_in_db(STATUS_STARTING, "")
        
        return {"message": "Sessão reiniciada. Aguarde alguns segundos..."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/disconnect")
async def disconnect():
    """Desconecta a sessão atual."""
    global driver, current_status, qr_code_base64
    
    print("🔌 Desconectando...")
    
    try:
        if driver:
            driver.quit()
            driver = None
        
        current_status = STATUS_STARTING
        qr_code_base64 = ""
        
        # Remove do banco
        await db.whatsapp_sessions.delete_one({"session_name": SESSION_NAME})
        
        return {"message": "Sessão desconectada"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MAIN ====================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════╗
    ║  WhatsApp QR Code Capture Service        ║
    ║  Port: 21466                              ║
    ║  Architecture: Selenium + Firefox         ║
    ╚═══════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=21466,
        log_level="info"
    )
