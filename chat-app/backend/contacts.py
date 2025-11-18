"""
Gerenciamento de contatos e conversas
"""
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from database import db

router = APIRouter(prefix="/contacts", tags=["contacts"])

# ============================================================================
# MODELS
# ============================================================================

class Contact(BaseModel):
    id: str
    name: str
    email: str
    avatar: Optional[str] = None
    lastMessage: Optional[str] = None
    lastMessageTime: Optional[int] = None
    unreadCount: int = 0
    online: bool = False

class ContactCreate(BaseModel):
    email: str
    name: Optional[str] = None

class ConversationMessage(BaseModel):
    id: str
    author: str
    text: str
    timestamp: int
    type: str = "text"
    status: Optional[str] = None
    attachment: Optional[dict] = None
    url: Optional[str] = None

# ============================================================================
# ROUTES
# ============================================================================

@router.get("/", response_model=List[Contact])
async def list_contacts(current_user: dict = Depends(lambda: None)):
    """
    Lista todos os usuários cadastrados como contatos
    (compatibilidade com mensagens antigas sem contactId)
    """
    # Por enquanto, retorna todos os usuários cadastrados
    users = await db.users.find({}, {"password": 0}).to_list(None)
    
    contacts = []
    for user in users:
        user_id = str(user["_id"])
        
        # Busca última mensagem (com ou sem contactId)
        last_msg = await db.messages.find_one(
            {"$or": [{"contactId": user_id}, {"userId": user_id}]},
            sort=[("createdAt", -1)]
        )
        
        contact = Contact(
            id=user_id,
            name=user.get("name", user["email"]),
            email=user["email"],
            avatar=user.get("avatar"),
            lastMessage=last_msg.get("text", "") if last_msg else "",
            lastMessageTime=int(last_msg["createdAt"].timestamp() * 1000) if last_msg else 0,
            unreadCount=0,
            online=False
        )
        contacts.append(contact)
    
    # Ordena por última mensagem
    contacts.sort(key=lambda c: c.lastMessageTime or 0, reverse=True)
    
    return contacts


class ConversationResponse(BaseModel):
    messages: List[ConversationMessage]
    hasMore: bool

@router.get("/{contact_id}/messages", response_model=ConversationResponse)
async def get_conversation(contact_id: str, limit: int = 50, before: Optional[int] = None):
    """
    Retorna mensagens de uma conversa específica com um contato
    """
    try:
        # Verifica se contato existe
        contact = await db.users.find_one({"_id": ObjectId(contact_id)})
        if not contact:
            raise HTTPException(404, "Contato não encontrado")
        
        contact_name = contact.get("name", contact["email"])
        
        # Filtro: mensagens desta conversa (suporta formato antigo e novo)
        # Formato novo: contactId = contact_id
        # Formato antigo: userId = contact_id OU author = contact_name
        query = {
            "$or": [
                {"contactId": contact_id},
                {"userId": contact_id},
                {"author": contact_name}
            ]
        }
        
        # Paginação
        if before:
            query["createdAt"] = {"$lt": {"$date": before}}
        
        # Busca mensagens
        cursor = db.messages.find(query).sort("createdAt", -1).limit(limit)
        messages = await cursor.to_list(None)
        messages.reverse()  # Ordem cronológica
        
        # Converte para response model
        result = []
        for msg in messages:
            from storage import presign_get
            
            message_dict = {
                "id": str(msg["_id"]),
                "author": msg.get("author", ""),
                "text": msg.get("text", ""),
                "timestamp": int(msg["createdAt"].timestamp() * 1000),
                "type": msg.get("type", "text"),
                "status": msg.get("status", "sent")
            }
            
            # Adiciona attachment se existir
            if "attachment" in msg:
                message_dict["attachment"] = msg["attachment"]
                message_dict["url"] = presign_get(msg["attachment"]["key"])
            
            result.append(ConversationMessage(**message_dict))
        
        return ConversationResponse(
            messages=result,
            hasMore=len(messages) == limit
        )
        
    except Exception as e:
        print(f"❌ Erro ao buscar conversa: {e}")
        raise HTTPException(500, f"Erro ao buscar conversa: {str(e)}")


@router.post("/{contact_id}/mark-read")
async def mark_conversation_read(contact_id: str):
    """
    Marca todas as mensagens de um contato como lidas
    """
    try:
        contact = await db.users.find_one({"_id": ObjectId(contact_id)})
        if not contact:
            raise HTTPException(404, "Contato não encontrado")
        
        contact_name = contact.get("name", contact["email"])
        
        # Atualiza status de mensagens não lidas do contato
        result = await db.messages.update_many(
            {
                "$or": [
                    {"userId": contact_id},
                    {"author": contact_name}
                ],
                "status": {"$ne": "read"}
            },
            {"$set": {"status": "read"}}
        )
        
        return {"updated": result.modified_count}
        
    except Exception as e:
        print(f"❌ Erro ao marcar como lido: {e}")
        raise HTTPException(500, f"Erro ao marcar como lido: {str(e)}")
