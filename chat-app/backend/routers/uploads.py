from typing import Optional
from datetime import datetime, timezone
import asyncio
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from deps import get_current_user_id
from storage import validate_upload, new_object_key, presign_put, presign_get, S3_BUCKET
from middleware.rate_limit import check_rate_limit, upload_limiter
from database import messages_collection
from transcription import transcribe_from_s3
from bots.ai_bot import is_ai_question, clean_bot_mention, ask_chatgpt
from socket_manager import sio

router = APIRouter(prefix="/uploads", tags=["uploads"])


class UploadRequest(BaseModel):
    filename: str
    mimetype: str
    size: int  # bytes


class UploadGrant(BaseModel):
    key: str
    putUrl: str


class ConfirmUploadIn(BaseModel):
    key: str
    filename: str
    mimetype: str
    author: str
    contactId: Optional[str] = None


@router.post("/grant", response_model=UploadGrant)
async def grant_upload(body: UploadRequest, request: Request, current_user_id: str = Depends(get_current_user_id)):
    # Rate limiting: 10 uploads por minuto por usuário
    check_rate_limit(request, upload_limiter, identifier=current_user_id)
    
    size_mb = max(1, body.size // (1024*1024))
    try:
        validate_upload(body.filename, body.mimetype, size_mb)
    except ValueError as e:
        raise HTTPException(400, str(e))
    key = new_object_key(body.filename)
    url = presign_put(key, body.mimetype)
    return {"key": key, "putUrl": url}


@router.post("/confirm")
async def confirm_upload(body: ConfirmUploadIn, current_user_id: str = Depends(get_current_user_id)):
    file_type = "file"
    if body.mimetype.startswith("image/"):
        file_type = "image"
    elif body.mimetype.startswith("audio/"):
        file_type = "audio"

    doc = {
        "author": body.author,
        "text": body.filename,
        "type": file_type,
        "status": "sent",
        "createdAt": datetime.now(timezone.utc),
        "userId": current_user_id,
        "contactId": body.contactId,
        "attachment": {
            "bucket": S3_BUCKET,
            "key": body.key,
            "filename": body.filename,
            "mimetype": body.mimetype
        }
    }
    result = await messages_collection.insert_one(doc)
    msg = {
        "id": str(result.inserted_id),
        "author": doc["author"],
        "text": doc["text"],
        "type": doc["type"],
        "status": doc["status"],
        "timestamp": int(doc["createdAt"].timestamp()*1000),
        "userId": current_user_id,
        "contactId": body.contactId,
        "attachment": doc["attachment"],
        "url": presign_get(body.key)
    }
    await sio.emit("chat:new-message", msg)

    # Transcrição de áudio (se aplicável)
    if file_type == "audio":
        from bots.automations import publish_message
        transcription = await transcribe_from_s3(body.key, S3_BUCKET)
        if transcription and not transcription.startswith("["):
            if is_ai_question(transcription):
                await sio.emit("chat:typing", {"author": "Guru", "isTyping": True})
                await asyncio.sleep(0.8)
                clean_text = clean_bot_mention(transcription)
                ai_response = await ask_chatgpt(clean_text, body.author, body.author)
                typing_time = len(ai_response) / 50
                typing_time = max(1.5, min(typing_time, 5.0))
                await asyncio.sleep(typing_time)
                await sio.emit("chat:typing", {"author": "Guru", "isTyping": False})
                response_text = f'🎤 _Áudio transcrito:_ "{transcription}"\n\n{ai_response}'
                await publish_message(sio.emit, author="Guru 🧠", text=response_text, user_id=body.author)

    return {"ok": True, "message": msg}
