from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MessageBase(BaseModel):
    author: str
    text: str
    status: Optional[str] = "sent"
    type: str = "text"

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
