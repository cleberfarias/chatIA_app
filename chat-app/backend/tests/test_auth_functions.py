"""
Testes para módulo de autenticação (auth.py)
Cobertura: hash_password, verify_password, create_access_token, decode_token, get_user_id_from_token
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt
import auth


def test_hash_password_creates_valid_hash():
    """Testa se hash_password gera hash válido"""
    password = "senha_segura_123"
    hashed = auth.hash_password(password)
    
    assert hashed is not None
    assert len(hashed) > 30  # Hash PBKDF2 é longo
    assert hashed != password  # Não deve ser texto plano
    assert hashed.startswith("$pbkdf2-sha256$")  # Formato esperado


def test_hash_password_generates_different_hashes():
    """Testa se mesma senha gera hashes diferentes (salt aleatório)"""
    password = "mesma_senha"
    hash1 = auth.hash_password(password)
    hash2 = auth.hash_password(password)
    
    assert hash1 != hash2  # Salt aleatório deve gerar hashes diferentes


def test_verify_password_with_correct_password():
    """Testa verificação com senha correta"""
    password = "senha_correta"
    hashed = auth.hash_password(password)
    
    assert auth.verify_password(password, hashed) is True


def test_verify_password_with_incorrect_password():
    """Testa verificação com senha incorreta"""
    password = "senha_correta"
    hashed = auth.hash_password(password)
    
    assert auth.verify_password("senha_errada", hashed) is False


def test_verify_password_with_empty_password():
    """Testa verificação com senha vazia"""
    hashed = auth.hash_password("alguma_senha")
    
    assert auth.verify_password("", hashed) is False


def test_create_access_token_generates_valid_jwt():
    """Testa criação de token JWT válido"""
    user_id = "user_123"
    token = auth.create_access_token(user_id)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 50  # JWT é longo
    assert token.count(".") == 2  # JWT tem 3 partes separadas por pontos


def test_create_access_token_contains_subject():
    """Testa se token contém o subject (user_id)"""
    user_id = "user_456"
    token = auth.create_access_token(user_id)
    
    # Decodifica sem validação para verificar payload
    payload = jwt.decode(token, auth.JWT_SECRET, algorithms=[auth.JWT_ALG])
    
    assert payload["sub"] == user_id


def test_create_access_token_contains_expiration():
    """Testa se token contém campo de expiração"""
    token = auth.create_access_token("user_789")
    
    payload = jwt.decode(token, auth.JWT_SECRET, algorithms=[auth.JWT_ALG])
    
    assert "exp" in payload
    assert "iat" in payload
    
    # Verifica se expiração é no futuro
    exp_timestamp = payload["exp"]
    iat_timestamp = payload["iat"]
    
    assert exp_timestamp > iat_timestamp


def test_create_access_token_expiration_time():
    """Testa se tempo de expiração está correto (60 minutos)"""
    token = auth.create_access_token("user_time")
    
    payload = jwt.decode(token, auth.JWT_SECRET, algorithms=[auth.JWT_ALG])
    
    exp = datetime.fromtimestamp(payload["exp"])
    iat = datetime.fromtimestamp(payload["iat"])
    
    diff = (exp - iat).total_seconds() / 60
    
    assert 59 <= diff <= 61  # Tolerância de 1 minuto


def test_decode_token_with_valid_token():
    """Testa decodificação de token válido"""
    user_id = "valid_user"
    token = auth.create_access_token(user_id)
    
    payload = auth.decode_token(token)
    
    assert payload is not None
    assert payload["sub"] == user_id
    assert "exp" in payload
    assert "iat" in payload


def test_decode_token_with_invalid_token():
    """Testa decodificação de token inválido"""
    invalid_token = "token.invalido.fake"
    
    with pytest.raises(ValueError) as exc_info:
        auth.decode_token(invalid_token)
    
    assert "Token inválido" in str(exc_info.value)


def test_decode_token_with_expired_token():
    """Testa decodificação de token expirado"""
    # Cria token com expiração no passado
    past_time = datetime.utcnow() - timedelta(hours=1)
    payload = {
        "sub": "expired_user",
        "iat": past_time,
        "exp": past_time + timedelta(seconds=1)
    }
    expired_token = jwt.encode(payload, auth.JWT_SECRET, algorithm=auth.JWT_ALG)
    
    with pytest.raises(ValueError) as exc_info:
        auth.decode_token(expired_token)
    
    assert "Token inválido" in str(exc_info.value)


def test_decode_token_with_wrong_secret():
    """Testa decodificação com secret incorreta"""
    # Cria token com secret diferente
    payload = {"sub": "user", "exp": datetime.utcnow() + timedelta(hours=1)}
    token_wrong_secret = jwt.encode(payload, "wrong_secret", algorithm=auth.JWT_ALG)
    
    with pytest.raises(ValueError) as exc_info:
        auth.decode_token(token_wrong_secret)
    
    assert "Token inválido" in str(exc_info.value)


def test_get_user_id_from_token_with_valid_token():
    """Testa extração de user_id de token válido"""
    user_id = "extract_user_123"
    token = auth.create_access_token(user_id)
    
    extracted_id = auth.get_user_id_from_token(token)
    
    assert extracted_id == user_id


def test_get_user_id_from_token_with_invalid_token():
    """Testa extração de user_id de token inválido"""
    with pytest.raises(ValueError):
        auth.get_user_id_from_token("invalid.token.here")


def test_get_user_id_from_token_without_sub():
    """Testa token sem campo 'sub'"""
    # Cria token sem 'sub'
    payload = {"exp": datetime.utcnow() + timedelta(hours=1)}
    token_no_sub = jwt.encode(payload, auth.JWT_SECRET, algorithm=auth.JWT_ALG)
    
    with pytest.raises(ValueError) as exc_info:
        auth.get_user_id_from_token(token_no_sub)
    
    assert "'sub' ausente" in str(exc_info.value)


def test_password_hash_is_deterministic_verification():
    """Testa que mesma senha sempre verifica contra mesmo hash"""
    password = "senha_fixa"
    hashed = auth.hash_password(password)
    
    # Múltiplas verificações devem todas passar
    for _ in range(5):
        assert auth.verify_password(password, hashed) is True


def test_different_passwords_different_verification():
    """Testa que senhas diferentes não verificam contra hashes errados"""
    password1 = "senha_um"
    password2 = "senha_dois"
    
    hash1 = auth.hash_password(password1)
    hash2 = auth.hash_password(password2)
    
    # Senha 1 não verifica contra hash 2
    assert auth.verify_password(password1, hash2) is False
    # Senha 2 não verifica contra hash 1
    assert auth.verify_password(password2, hash1) is False


def test_token_roundtrip():
    """Testa ciclo completo: criar token → decodificar → extrair user_id"""
    user_id = "roundtrip_user"
    
    # Cria token
    token = auth.create_access_token(user_id)
    
    # Decodifica
    payload = auth.decode_token(token)
    assert payload["sub"] == user_id
    
    # Extrai user_id
    extracted = auth.get_user_id_from_token(token)
    assert extracted == user_id


def test_special_characters_in_user_id():
    """Testa user_id com caracteres especiais"""
    user_id = "user@example.com|123"
    token = auth.create_access_token(user_id)
    
    extracted = auth.get_user_id_from_token(token)
    assert extracted == user_id


def test_long_user_id():
    """Testa user_id muito longo"""
    user_id = "a" * 500
    token = auth.create_access_token(user_id)
    
    extracted = auth.get_user_id_from_token(token)
    assert extracted == user_id
    assert len(extracted) == 500
