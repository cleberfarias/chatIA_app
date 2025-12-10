#!/usr/bin/env python3
import time
import requests
import socketio

API_URL = 'http://localhost:3000'

# Register a user (if not exists) and log in
email = 'test_agent@example.com'
password = 'password123'
name = 'Test Agent'

# Attempt to register; ignore if already exists
try:
    requests.post(f'{API_URL}/auth/register', json={'email': email, 'name': name, 'password': password}, timeout=5)
except Exception as e:
    pass

# Login
resp = requests.post(f'{API_URL}/auth/login', json={'email': email, 'password': password}, timeout=5)
resp.raise_for_status()
_login = resp.json()
TOKEN = _login['access_token']
user = _login['user']

print('Got token', TOKEN[:40])

# Connect to Socket.IO
sio = socketio.Client()

@sio.event
def connect():
    print('Connected to socket')

@sio.on('agent:message')
def on_agent_message(data):
    print('Agent message:', data)

@sio.on('agent:error')
def on_agent_error(data):
    print('Agent error:', data)

@sio.on('agent:opened')
def on_agent_opened(data):
    print('Agent opened', data)

@sio.on('agent:closed')
def on_agent_closed(data):
    print('Agent closed', data)

sio.connect(API_URL, namespaces=['/'], auth={'token': TOKEN})

# Open SDR agent for current contact (we'll fake a contactId)
contact_id = None
# try to get a contact id to attach; fallback to using None (server supports None?)
try:
    contacts_resp = requests.get(f'{API_URL}/contacts', headers={'Authorization': f'Bearer {TOKEN}'})
    contacts_resp.raise_for_status()
    contacts = contacts_resp.json().get('contacts', [])
    if contacts:
        contact_id = contacts[0]['id']
except Exception as e:
    print('Could not fetch contacts', e)

if not contact_id:
    print('No contact id found; creating temporary contact')
    try:
        r = requests.post(f'{API_URL}/contacts', headers={'Authorization': f'Bearer {TOKEN}'}, json={'name': 'Test Contact', 'phone': '+5511999999999'})
        r.raise_for_status()
        contact_id = r.json()['id']
    except Exception as e:
        print('Could not create contact', e)

# Send agent:open
sio.emit('agent:open', {'agentKey': 'sdr', 'contactId': contact_id})

time.sleep(1)

# send agent:send
sio.emit('agent:send', {'agentKey': 'sdr', 'message': 'Qual a próxima ação para esse cliente?', 'userId': user['id'], 'userName': user['name'], 'contactId': contact_id})

# Wait for response
for _ in range(20):
    time.sleep(1)

sio.disconnect()
print('Disconnected')
