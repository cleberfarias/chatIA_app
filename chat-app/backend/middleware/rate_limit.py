"""
Middleware de Rate Limiting para proteção contra abuse.

Protege endpoints críticos limitando número de requisições por IP/usuário.
"""
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter simples baseado em memória.
    
    Para produção, considere usar Redis para persistência entre instâncias.
    """
    
    def __init__(self, max_requests: int, window_seconds: int, name: str = "default"):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
        self.name = name
    
    def check(self, key: str) -> bool:
        """
        Verifica se a chave (IP/user_id) excedeu o limite.
        
        Args:
            key: Identificador único (IP address ou user_id)
            
        Returns:
            True se permitido, False se excedeu limite
        """
        now = datetime.now()
        cutoff = now - self.window
        
        # Remove requisições antigas (fora da janela)
        self.requests[key] = [
            req for req in self.requests[key]
            if req > cutoff
        ]
        
        # Verifica limite
        current_count = len(self.requests[key])
        if current_count >= self.max_requests:
            logger.warning(
                f"Rate limit excedido - {self.name}: {key} "
                f"({current_count}/{self.max_requests} em {self.window.seconds}s)"
            )
            return False
        
        # Registra nova requisição
        self.requests[key].append(now)
        return True
    
    def reset(self, key: str):
        """Reset o contador para uma chave específica."""
        if key in self.requests:
            del self.requests[key]


# Limitadores pré-configurados por tipo de operação
login_limiter = RateLimiter(
    max_requests=5, 
    window_seconds=300,  # 5 tentativas por 5 minutos
    name="login"
)

register_limiter = RateLimiter(
    max_requests=3,
    window_seconds=3600,  # 3 registros por hora
    name="register"
)

upload_limiter = RateLimiter(
    max_requests=10,
    window_seconds=60,  # 10 uploads por minuto
    name="upload"
)

message_limiter = RateLimiter(
    max_requests=100,
    window_seconds=60,  # 100 mensagens por minuto
    name="message"
)

api_limiter = RateLimiter(
    max_requests=1000,
    window_seconds=60,  # 1000 requests por minuto (geral)
    name="api_general"
)


def check_rate_limit(request: Request, limiter: RateLimiter, identifier: str = None):
    """
    Helper function para verificar rate limit em uma rota.
    
    Args:
        request: FastAPI Request object
        limiter: Instância do RateLimiter
        identifier: Identificador customizado (opcional, usa IP por padrão)
        
    Raises:
        HTTPException: 429 se limite excedido
    """
    key = identifier or request.client.host
    
    if not limiter.check(key):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "too_many_requests",
                "message": f"Muitas requisições. Tente novamente em {limiter.window.seconds} segundos.",
                "retry_after": limiter.window.seconds
            }
        )
