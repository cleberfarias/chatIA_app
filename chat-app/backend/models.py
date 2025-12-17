from pydantic import BaseModel, Field, ConfigDict, field_serializer, EmailStr, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import re
import html


class AttachmentInfo(BaseModel):
    """Informações do anexo armazenado no S3/MinIO"""
    bucket: str
    key: str
    filename: str
    mimetype: str


class MessageBase(BaseModel):
    author: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1, max_length=5000)
    status: Optional[str] = "sent"
    type: str = "text"  # "text" | "image" | "file"
    attachment: Optional[AttachmentInfo] = None
    contactId: Optional[str] = None  # 🆕 ID do contato da conversa
    
    @field_validator('text')
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """
        Sanitiza texto para prevenir XSS e injection attacks.
        
        - Remove tags HTML/script
        - Escapa caracteres especiais
        - Mantém quebras de linha e texto básico
        """
        if not v:
            return v
        
        # Remove scripts e tags perigosas
        v = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.DOTALL | re.IGNORECASE)
        v = re.sub(r'<iframe[^>]*>.*?</iframe>', '', v, flags=re.DOTALL | re.IGNORECASE)
        v = re.sub(r'<object[^>]*>.*?</object>', '', v, flags=re.DOTALL | re.IGNORECASE)
        v = re.sub(r'<embed[^>]*>.*?</embed>', '', v, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove todas as tags HTML (mantém o texto)
        v = re.sub(r'<[^>]+>', '', v)
        
        # Escapa entidades HTML
        v = html.escape(v, quote=False)
        
        return v.strip()
    
    @field_validator('author')
    @classmethod
    def sanitize_author(cls, v: str) -> str:
        """
        Valida nome do autor.
        
        - Permite letras, números, espaços e alguns caracteres especiais
        - Remove caracteres potencialmente perigosos
        """
        if not v:
            raise ValueError('Nome do autor não pode ser vazio')
        
        # Remove caracteres especiais perigosos
        v = re.sub(r'[<>{}[\]\\\/]', '', v)
        
        # Valida comprimento
        v = v.strip()
        if len(v) < 1:
            raise ValueError('Nome do autor muito curto')
        if len(v) > 100:
            raise ValueError('Nome do autor muito longo')
        
        return v


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: str = Field(alias="_id")
    createdAt: datetime
    model_config = ConfigDict(populate_by_name=True)

    @field_serializer("createdAt")
    def _serialize_created_at(self, v: datetime) -> int:
        return int(v.timestamp() * 1000)


class MessageResponse(BaseModel):
    id: str
    author: str
    text: str
    timestamp: int
    status: str
    type: str
    attachment: Optional[AttachmentInfo] = None
    url: Optional[str] = None  # URL assinada para acesso ao arquivo


class InteractionLog(BaseModel):
    """Registro de interação para análise de NLU e entidades"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    agent: Optional[str] = None  # Nome do agente usado
    question: str
    response: str
    intent: Optional[str] = None  # Intent detectado pelo NLU
    intent_confidence: Optional[float] = None
    entities: Optional[Dict[str, Any]] = None  # Entidades extraídas
    rating: Optional[int] = None  # 1-5 avaliação do usuário
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(populate_by_name=True)


class HandoverReason(str, Enum):
    """Motivos para transferência bot→humano"""
    explicit_request = "explicit_request"
    low_confidence = "low_confidence"
    complaint = "complaint"
    complex_query = "complex_query"
    escalation = "escalation"
    technical_issue = "technical_issue"
    outside_hours = "outside_hours"


class HandoverStatus(str, Enum):
    """Status da transferência"""
    pending = "pending"
    accepted = "accepted"
    in_progress = "in_progress"
    resolved = "resolved"
    cancelled = "cancelled"
    timeout = "timeout"


class HandoverRequest(BaseModel):
    """Requisição de transferência bot→humano"""
    id: Optional[str] = Field(None, alias="_id")
    customer_id: str
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    reason: HandoverReason
    status: HandoverStatus = HandoverStatus.pending
    priority: int = Field(ge=1, le=4)  # 1=baixa, 4=urgente
    last_messages: List[str] = []
    entities_extracted: Optional[Dict[str, Any]] = None
    intent: Optional[str] = None
    context_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    assigned_agent: Optional[str] = None
    tags: List[str] = []
    model_config = ConfigDict(populate_by_name=True)


class CalendarEvent(BaseModel):
    """Evento agendado no Google Calendar"""
    id: Optional[str] = Field(None, alias="_id")
    google_event_id: str  # ID do evento no Google Calendar
    customer_id: str
    customer_name: str
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    timezone: str = "America/Sao_Paulo"
    location: Optional[str] = None
    attendees: List[EmailStr] = []
    meet_link: Optional[str] = None  # Link do Google Meet
    calendar_link: Optional[str] = None  # Link do evento no Google Calendar
    status: str = "scheduled"  # scheduled, confirmed, cancelled, completed
    reminder_sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    notes: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)
