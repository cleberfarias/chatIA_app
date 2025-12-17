import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from socket_manager import sio, create_socket_app
from socket_handlers import register_socket_handlers
from bots.automations import start_scheduler, load_and_schedule_all
from middleware.security import add_security_headers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria índices do MongoDB
    from database import create_indexes
    await create_indexes()
    print("✅ Índices do MongoDB criados")
    # Carrega bots customizados salvos
    from bots.agents import load_custom_agents_from_db
    await load_custom_agents_from_db()
    print("✅ Bots customizados carregados")
    
    # Inicia scheduler e automações
    start_scheduler()
    await load_and_schedule_all(sio.emit)
    print("✅ Scheduler iniciado e automações carregadas")
    yield

# FastAPI app
app = FastAPI(title="Chat API", lifespan=lifespan)

# CORS configurável
# CORS configuration – ensure localhost dev ports covered even when Vite switches ports
allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")]

if "http://localhost:5173" in allowed_origins and "http://localhost:5174" not in allowed_origins:
    allowed_origins.append("http://localhost:5174")

if "http://127.0.0.1:5173" in allowed_origins and "http://127.0.0.1:5174" not in allowed_origins:
    allowed_origins.append("http://127.0.0.1:5174")

allow_credentials = "*" not in allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers
add_security_headers(app)
print("✅ Security headers configurados")

# Routers
try:
    from users import router as auth_router
    app.include_router(auth_router)
    print("✅ Rotas de autenticação carregadas")
except ImportError:
    print("⚠️  Arquivo users.py não encontrado - autenticação não disponível")

try:
    from contacts import router as contacts_router
    app.include_router(contacts_router)
    print("✅ Rotas de contatos carregadas")
except ImportError:
    print("⚠️  Arquivo contacts.py não encontrado - contatos não disponíveis")

from routers.messages import router as messages_router
app.include_router(messages_router)

from routers.custom_bots import router as custom_bots_router
app.include_router(custom_bots_router)

from routers.automations import router as automations_router
app.include_router(automations_router)

from routers.uploads import router as uploads_router
app.include_router(uploads_router)

from routers.webhooks import router as webhooks_router
app.include_router(webhooks_router)

try:
    from routers.omni import router as omni_router
    app.include_router(omni_router)
    print("✅ Router omnichannel carregado")
except ImportError as e:
    print(f"⚠️  Router omnichannel não encontrado: {e}")

from routers.nlu import router as nlu_router
app.include_router(nlu_router)

from routers.handovers import router as handovers_router
app.include_router(handovers_router)

from routers.calendar import router as calendar_router
app.include_router(calendar_router)


@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Chat API running with Python"}

# Socket.IO
register_socket_handlers()
socket_app = create_socket_app(app)
