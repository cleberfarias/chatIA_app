"""
Middleware de segurança para adicionar headers HTTP de proteção.

Headers implementados:
- X-Content-Type-Options: Previne MIME type sniffing
- X-Frame-Options: Previne clickjacking
- X-XSS-Protection: Proteção contra XSS (legado, mas mantido)
- Strict-Transport-Security: Força HTTPS (apenas em produção)
- Content-Security-Policy: Política de segurança de conteúdo
- Referrer-Policy: Controla envio de referrer
"""
import os
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adiciona headers de segurança em todas as respostas.
    """
    
    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.environment = environment
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Previne MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Previne clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Proteção XSS (legacy, mas mantido para compatibilidade)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Política de referrer
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        # Permite conexões WebSocket e recursos da mesma origem
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Vue precisa de unsafe-eval
            "style-src 'self' 'unsafe-inline'",  # Vuetify usa inline styles
            "img-src 'self' data: blob: http: https:",
            "font-src 'self' data:",
            "connect-src 'self' ws: wss: http: https:",  # WebSocket
            "media-src 'self' blob: http: https:",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # HSTS - Apenas em produção com HTTPS
        if self.environment == "production":
            # Força HTTPS por 1 ano
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Remove header que expõe tecnologia do servidor
        response.headers.pop("Server", None)
        
        return response


def add_security_headers(app):
    """
    Helper function para adicionar middleware de segurança.
    
    Usage:
        from middleware.security import add_security_headers
        add_security_headers(app)
    """
    environment = os.getenv("ENVIRONMENT", "development")
    app.add_middleware(SecurityHeadersMiddleware, environment=environment)
