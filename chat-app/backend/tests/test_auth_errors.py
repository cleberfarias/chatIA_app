from fastapi.testclient import TestClient

from backend import main


def test_agents_messages_requires_auth():
    client = TestClient(main.app)
    resp = client.get("/agents/test/messages")
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Não autenticado"


def test_agents_messages_invalid_token():
    client = TestClient(main.app)
    resp = client.get("/agents/test/messages", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401
    # Mensagem deve informar motivo (ex: Token inválido)
    assert "Token inválido" in resp.json().get("detail", "")
