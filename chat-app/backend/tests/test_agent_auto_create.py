import pytest
from backend import socket_handlers


def test_agent_auto_create_map():
    # Manipula o mapa diretamente
    key = ('user123', 'sdr')
    socket_handlers.agent_auto_create_per_user[key] = True
    assert socket_handlers.agent_auto_create_per_user.get(key) is True
    del socket_handlers.agent_auto_create_per_user[key]
    assert key not in socket_handlers.agent_auto_create_per_user
