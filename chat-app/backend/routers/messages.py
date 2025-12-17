from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Depends, Request
from bson import ObjectId

from database import messages_collection
from storage import presign_get
from deps import get_current_user_id

router = APIRouter(prefix="", tags=["messages"])


@router.get("/messages")
async def get_messages(
    before: Optional[int] = None,
    limit: int = Query(default=30, le=100),
    contact_id: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id)
):
    filters = []
    if contact_id:
        filters.append({
            "$or": [
                {"userId": current_user_id, "contactId": contact_id},
                {"userId": contact_id, "contactId": current_user_id}
            ]
        })
    else:
        filters.append({"$or": [{"userId": current_user_id}, {"contactId": current_user_id}]})

    if before:
        before_dt = datetime.fromtimestamp(before / 1000)
        filters.append({"createdAt": {"$lt": before_dt}})

    query = filters[0] if len(filters) == 1 else {"$and": filters}

    cursor = messages_collection.find(query).sort("createdAt", -1).limit(limit)
    docs = await cursor.to_list(length=limit)

    messages = []
    for doc in reversed(docs):
        msg_dict = {
            "id": str(doc["_id"]),
            "author": doc["author"],
            "text": doc["text"],
            "timestamp": int(doc["createdAt"].timestamp() * 1000),
            "status": doc.get("status", "sent"),
            "type": doc.get("type", "text")
        }
        if "attachment" in doc:
            msg_dict["attachment"] = doc["attachment"]
            msg_dict["url"] = presign_get(doc["attachment"]["key"])
        messages.append(msg_dict)

    return {
        "messages": messages,
        "hasMore": len(docs) == limit
    }


@router.get("/agents/{agent_key}/messages")
async def get_agent_messages(
    agent_key: str,
    request: Request,
    contact_id: Optional[str] = Query(None, alias="contactId"),
    before: Optional[int] = None,
    limit: int = Query(default=30, le=100)
):
    from database import agent_messages_collection
    from auth import get_user_id_from_token

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    try:
        user_id = get_user_id_from_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    query = {
        "agentKey": agent_key,
        "userId": user_id
    }
    if contact_id:
        query["contactId"] = contact_id
    if before:
        before_dt = datetime.fromtimestamp(before / 1000)
        query["createdAt"] = {"$lt": before_dt}

    cursor = agent_messages_collection.find(query).sort("createdAt", -1).limit(limit)
    docs = await cursor.to_list(length=limit)

    messages = []
    for doc in reversed(docs):
        messages.append({
            "id": str(doc["_id"]),
            "author": doc["author"],
            "text": doc["text"],
            "timestamp": int(doc["createdAt"].timestamp() * 1000),
            "agentKey": doc["agentKey"]
        })

    return {
        "messages": messages,
        "hasMore": len(docs) == limit
    }


@router.delete("/messages/all")
async def delete_all_messages(current_user_id: str = Depends(get_current_user_id)):
    """Limpa todas as mensagens do banco de dados"""
    from database import agent_messages_collection
    
    # Deleta mensagens normais
    result_messages = await messages_collection.delete_many({})
    
    # Deleta mensagens de agentes
    result_agents = await agent_messages_collection.delete_many({})
    
    return {
        "success": True,
        "deleted": {
            "messages": result_messages.deleted_count,
            "agentMessages": result_agents.deleted_count
        }
    }
