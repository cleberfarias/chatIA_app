from motor.motor_asyncio import AsyncIOMotorClient
from os import getenv

DATABASE_URL = getenv("DATABASE_URL", "mongodb://mongo:27017/chatdb?replicaSet=rs0")

# Cliente MongoDB assíncrono
client = AsyncIOMotorClient(DATABASE_URL)
db = client.chatdb
messages_collection = db.messages
