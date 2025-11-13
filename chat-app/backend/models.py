from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AttachmentInfo(BaseModel):
    """Informações do anexo armazenado no S3/MinIO"""
    bucket: str
    key: str
    filename: str
    mimetype: str


class MessageBase(BaseModel):
    author: str
    text: str
    status: Optional[str] = "sent"
    type: str = "text"  # "text" | "image" | "file"
    attachment: Optional[AttachmentInfo] = None


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: str = Field(alias="_id")
    createdAt: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: int(v.timestamp() * 1000)  # Converte para timestamp
        }


class MessageResponse(BaseModel):
    id: str
    author: str
    text: str
    timestamp: int
    status: str
    type: str
    attachment: Optional[AttachmentInfo] = None
    url: Optional[str] = None  # URL assinada para acesso ao arquivo
