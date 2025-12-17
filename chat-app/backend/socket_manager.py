import socketio
import os

# Configurar Redis adapter para clustering (múltiplas instâncias)
REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    # Com Redis: suporta múltiplas instâncias da API
    print(f"✅ Socket.IO configurado com Redis adapter: {REDIS_URL}")
    client_manager = socketio.AsyncRedisManager(REDIS_URL)
else:
    # Sem Redis: apenas uma instância (desenvolvimento)
    print("⚠️  Socket.IO sem Redis - apenas 1 instância suportada")
    client_manager = None

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    client_manager=client_manager
)


def create_socket_app(app):
    """Cria ASGI app do Socket.IO acoplado ao FastAPI app."""
    return socketio.ASGIApp(sio, app)
