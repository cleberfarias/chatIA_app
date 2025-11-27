"""
Rotas para gerenciamento de eventos do Google Calendar.

Endpoints para criar, listar, atualizar e cancelar agendamentos.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, date
from bson import ObjectId

from models import CalendarEvent
from database import calendar_events_collection
from deps import get_current_user_id
from integrations.google_calendar import GoogleCalendarService

router = APIRouter(prefix="/calendar", tags=["Calendar"])

# Instância global do serviço (poderia ser injetado via Depends)
calendar_service = GoogleCalendarService()


class CreateEventRequest(BaseModel):
    """Request para criar evento no calendário"""
    customer_id: str
    customer_name: str
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    notes: Optional[str] = None


class UpdateEventRequest(BaseModel):
    """Request para atualizar evento"""
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    notes: Optional[str] = None


@router.get("/auth-status")
async def check_auth_status():
    """
    Verifica se o Google Calendar está autenticado.
    
    Returns:
        Status da autenticação
    """
    try:
        is_authenticated = calendar_service.authenticate()
        return {
            "authenticated": is_authenticated,
            "message": "Google Calendar conectado" if is_authenticated else "Autenticação necessária"
        }
    except Exception as e:
        return {
            "authenticated": False,
            "message": f"Erro: {str(e)}"
        }


@router.post("/events", status_code=201)
async def create_calendar_event(
    request: CreateEventRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Cria um evento no Google Calendar e registra no banco.
    
    Args:
        request: Dados do evento
        current_user: Usuário autenticado
        
    Returns:
        Evento criado com links
    """
    try:
        # Cria evento no Google Calendar
        attendees = [request.customer_email]
        
        google_event = calendar_service.create_meeting_event(
            summary=request.title,
            description=request.description or "",
            start_datetime=request.start_time,
            end_datetime=request.end_time,
            attendee_emails=attendees,
            location=request.location,
            send_notifications=True
        )
        
        if not google_event:
            raise HTTPException(status_code=500, detail="Falha ao criar evento no Google Calendar")
        
        # Registra no banco
        event_data = {
            "google_event_id": google_event["id"],
            "customer_id": request.customer_id,
            "customer_name": request.customer_name,
            "customer_email": request.customer_email,
            "customer_phone": request.customer_phone,
            "agent_id": user_id,
            "agent_name": user_id,
            "title": request.title,
            "description": request.description,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "location": request.location,
            "attendees": attendees,
            "meet_link": google_event.get("hangoutLink"),
            "calendar_link": google_event.get("htmlLink"),
            "status": "scheduled",
            "created_at": datetime.utcnow(),
            "notes": request.notes
        }
        
        result = await calendar_events_collection.insert_one(event_data)
        
        return {
            "id": str(result.inserted_id),
            "google_event_id": google_event["id"],
            "meet_link": google_event.get("hangoutLink"),
            "calendar_link": google_event.get("htmlLink"),
            "status": "scheduled",
            "message": "Evento criado com sucesso! Convite enviado por email."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar evento: {str(e)}")


@router.get("/events")
async def list_events(
    customer_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """
    Lista eventos do calendário com filtros.
    
    Args:
        customer_id: Filtrar por cliente
        agent_id: Filtrar por agente
        status: Filtrar por status
        start_date: Data inicial
        end_date: Data final
        limit: Máximo de resultados
        current_user: Usuário autenticado
        
    Returns:
        Lista de eventos
    """
    try:
        query = {}
        
        if customer_id:
            query["customer_id"] = customer_id
        if agent_id:
            query["agent_id"] = agent_id
        if status:
            query["status"] = status
        
        # Filtro de data
        if start_date or end_date:
            query["start_time"] = {}
            if start_date:
                query["start_time"]["$gte"] = datetime.combine(start_date, datetime.min.time())
            if end_date:
                query["start_time"]["$lte"] = datetime.combine(end_date, datetime.max.time())
        
        cursor = calendar_events_collection.find(query).sort("start_time", 1).limit(limit)
        events = await cursor.to_list(length=limit)
        
        # Converte ObjectId
        for event in events:
            event["id"] = str(event.pop("_id"))
        
        return events
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar eventos: {str(e)}")


@router.get("/events/{event_id}")
async def get_event(
    event_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Busca um evento específico.
    
    Args:
        event_id: ID do evento no banco
        current_user: Usuário autenticado
        
    Returns:
        Dados do evento
    """
    try:
        event = await calendar_events_collection.find_one({"_id": ObjectId(event_id)})
        
        if not event:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        
        event["id"] = str(event.pop("_id"))
        return event
        
    except Exception as e:
        if "not a valid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="ID inválido")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar evento: {str(e)}")


@router.put("/events/{event_id}")
async def update_event(
    event_id: str,
    request: UpdateEventRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Atualiza um evento no Google Calendar e no banco.
    
    Args:
        event_id: ID do evento
        request: Dados a atualizar
        current_user: Usuário autenticado
        
    Returns:
        Evento atualizado
    """
    try:
        # Busca evento no banco
        event = await calendar_events_collection.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        
        # Monta updates para Google Calendar
        google_updates = {}
        db_updates = {}
        
        if request.title:
            google_updates["summary"] = request.title
            db_updates["title"] = request.title
        if request.description:
            google_updates["description"] = request.description
            db_updates["description"] = request.description
        if request.location:
            google_updates["location"] = request.location
            db_updates["location"] = request.location
        if request.notes:
            db_updates["notes"] = request.notes
        
        # Atualiza datas se fornecidas
        if request.start_time:
            google_updates["start"] = {
                "dateTime": request.start_time.isoformat(),
                "timeZone": "America/Sao_Paulo"
            }
            db_updates["start_time"] = request.start_time
        if request.end_time:
            google_updates["end"] = {
                "dateTime": request.end_time.isoformat(),
                "timeZone": "America/Sao_Paulo"
            }
            db_updates["end_time"] = request.end_time
        
        # Atualiza no Google Calendar
        if google_updates:
            updated_google = calendar_service.update_event(
                event["google_event_id"],
                google_updates,
                send_notifications=True
            )
            if not updated_google:
                raise HTTPException(status_code=500, detail="Falha ao atualizar no Google Calendar")
        
        # Atualiza no banco
        db_updates["updated_at"] = datetime.utcnow()
        await calendar_events_collection.update_one(
            {"_id": ObjectId(event_id)},
            {"$set": db_updates}
        )
        
        return {"message": "Evento atualizado com sucesso"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar evento: {str(e)}")


@router.delete("/events/{event_id}")
async def cancel_event(
    event_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Cancela um evento (deleta do Google Calendar e marca como cancelado).
    
    Args:
        event_id: ID do evento
        current_user: Usuário autenticado
        
    Returns:
        Confirmação
    """
    try:
        # Busca evento
        event = await calendar_events_collection.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        
        # Cancela no Google Calendar
        success = calendar_service.cancel_event(
            event["google_event_id"],
            send_notifications=True
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Falha ao cancelar no Google Calendar")
        
        # Marca como cancelado no banco
        await calendar_events_collection.update_one(
            {"_id": ObjectId(event_id)},
            {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()}}
        )
        
        return {"message": "Evento cancelado com sucesso. Notificações enviadas."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar evento: {str(e)}")


@router.get("/availability")
async def check_availability(
    date: date = Query(..., description="Data para verificar"),
    start_time: str = Query(..., description="Hora inicial (HH:MM)"),
    end_time: str = Query(..., description="Hora final (HH:MM)")
):
    """
    Verifica se um horário está disponível.
    
    Args:
        date: Data da reunião
        start_time: Hora de início
        end_time: Hora de término
        
    Returns:
        Disponibilidade do horário
    """
    try:
        is_available = calendar_service.check_time_slot_available(
            date, start_time, end_time
        )
        
        return {
            "date": date.isoformat(),
            "start_time": start_time,
            "end_time": end_time,
            "available": is_available,
            "message": "Horário disponível" if is_available else "Horário já ocupado"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar disponibilidade: {str(e)}")


@router.get("/available-slots")
async def get_available_slots(
    date: date = Query(..., description="Data para buscar horários"),
    duration_minutes: int = Query(60, ge=15, le=240, description="Duração do slot em minutos")
):
    """
    Retorna todos os horários disponíveis em um dia.
    
    Args:
        date: Data para verificar
        duration_minutes: Duração desejada do slot
        
    Returns:
        Lista de horários livres
    """
    try:
        slots = calendar_service.get_available_slots(
            date,
            slot_duration_minutes=duration_minutes
        )
        
        return {
            "date": date.isoformat(),
            "duration_minutes": duration_minutes,
            "available_slots": slots,
            "count": len(slots)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar slots: {str(e)}")
