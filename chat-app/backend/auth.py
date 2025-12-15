from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
import os

"""
Usamos PBKDF2-SHA256 por compatibilidade no container (evita dependência nativa do bcrypt).
Se preferir bcrypt, troque para schemes=["bcrypt"] e garanta versão compatível do pacote bcrypt.
"""
PWD_CTX = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret_change_in_production")
JWT_ALG = "HS256"
ACCESS_TTL_MIN = 60

def hash_password(password: str) -> str:
    """Hash de senha com bcrypt"""
    return PWD_CTX.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    return PWD_CTX.verify(plain_password, hashed_password)

def create_access_token(sub: str) -> str:
    """Cria token JWT com expiração"""
    now = datetime.utcnow()
    payload = {
        "sub": sub,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TTL_MIN)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> dict:
    """Decodifica e valida token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload
    except JWTError as e:
        raise ValueError(f"Token inválido: {e}")

def get_user_id_from_token(token: str) -> str:
    """Extrai o userId (sub) do token JWT"""
    # decode_token já levanta ValueError com motivo (ex: token inválido/expirado)
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Token inválido: 'sub' ausente")
    return user_id