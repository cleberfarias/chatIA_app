#!/usr/bin/env python3
import time
import requests
import socketio

API_URL = 'http://localhost:3000'

# Login
email = 'test_agent@example.com'
password = 'password123'

# Login
resp = requests.post(f'{API_URL}/auth/login', json={'email': email, 'password': password}, timeout=5)
resp.raise_for_status()
_login = resp.json()
TOKEN = _login['access_token']
user = _login['user']

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to socket')

@sio.on('agent:error')
def on_agent_error(data):
    print('Agent error:', data)

sio.connect(API_URL, namespaces=['/'], auth={'token': TOKEN})

# Send unknown agentKey
contact_id = None
sio.emit('agent:send', {'agentKey': 'unknown', 'message': 'Teste de erro', 'userId': user['id'], 'userName': user['name'], 'contactId': contact_id})

# Wait for response
for _ in range(5):
    time.sleep(1)

sio.disconnect()
print('Disconnected')
