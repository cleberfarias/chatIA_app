from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from datetime import datetime
from database import db
from auth import hash_password, verify_password, create_access_token
from middleware.rate_limit import check_rate_limit, login_limiter, register_limiter


router = APIRouter(prefix="/auth", tags=["auth"])
users = db.users


class RegisterIn(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(data: RegisterIn, request: Request):
    """Registra novo usuário"""
    # Rate limiting: 3 registros por hora por IP
    check_rate_limit(request, register_limiter)
    
    if await users.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    doc = {
        "email": data.email,
        "name": data.name,
        "password": hash_password(data.password),
        "role": "user",
        "created_at": datetime.utcnow()
    }
    
    await users.insert_one(doc)
    return {"message": "Usuário registrado com sucesso"}


@router.post("/login")
async def login(data: LoginIn, request: Request):
    """Autentica usuário e retorna token JWT"""
    # Rate limiting: 5 tentativas por 5 minutos por IP
    check_rate_limit(request, login_limiter)
    
    user = await users.find_one({"email": data.email})
    
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    token = create_access_token(str(user["_id"]))
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"]
        }
    }  