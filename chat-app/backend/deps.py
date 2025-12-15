from fastapi import HTTPException, Request
from auth import get_user_id_from_token


def get_current_user_id(request: Request) -> str:
    """Extrai e valida o user_id do token JWT; exige autenticação."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Token ausente")
    try:
        user_id = get_user_id_from_token(token)
    except ValueError as e:
        # Propaga a mensagem original (ex: token expirado / inválido)
        raise HTTPException(status_code=401, detail=str(e))
    return user_id
