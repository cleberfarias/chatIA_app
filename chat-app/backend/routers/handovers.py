"""
Rotas para gerenciamento de handover (transferências bot→humano).

Endpoints para criar, listar, aceitar e resolver transferências.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from models import HandoverRequest, HandoverStatus, HandoverReason
from database import handovers_collection
from deps import get_current_user_id
from bots.handover import (
    should_trigger_handover,
    generate_handover_summary,
    suggest_agent_for_handover,
    get_handover_message_for_customer,
    calculate_priority
)

router = APIRouter(prefix="/handovers", tags=["Handover"])


class CreateHandoverRequest(BaseModel):
    """Request para criar handover"""
    customer_id: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    reason: HandoverReason
    last_messages: List[str] = []
    entities_extracted: Optional[Dict[str, Any]] = None
    intent: Optional[str] = None


class AcceptHandoverRequest(BaseModel):
    """Request para aceitar handover"""
    agent_id: str
    agent_name: str


class ResolveHandoverRequest(BaseModel):
    """Request para resolver handover"""
    resolution_notes: Optional[str] = None


@router.post("/", status_code=201)
async def create_handover(
    request: CreateHandoverRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Cria uma requisição de handover (transferência bot→humano).
    
    Args:
        request: Dados do handover
        current_user: Usuário autenticado
        
    Returns:
        Handover criado com ID e mensagem para o cliente
    """
    try:
        # Calcula prioridade
        priority = calculate_priority(
            request.reason,
            request.entities_extracted or {},
            request.intent
        )
        
        # Gera resumo do contexto
        context_summary = generate_handover_summary(
            request.last_messages,
            request.entities_extracted,
            request.intent
        )
        
        # Sugere agente/departamento
        suggested_department = suggest_agent_for_handover(
            request.reason,
            request.intent,
            request.entities_extracted
        )
        
        # Cria handover
        handover_data = {
            "customer_id": request.customer_id,
            "customer_name": request.customer_name,
            "customer_email": request.customer_email,
            "customer_phone": request.customer_phone,
            "reason": request.reason.value,
            "status": HandoverStatus.pending.value,
            "priority": priority,
            "last_messages": request.last_messages,
            "entities_extracted": request.entities_extracted,
            "intent": request.intent,
            "context_summary": context_summary,
            "created_at": datetime.utcnow(),
            "tags": [suggested_department]
        }
        
        result = await handovers_collection.insert_one(handover_data)
        handover_id = str(result.inserted_id)
        
        # Mensagem para o cliente
        customer_message = get_handover_message_for_customer(request.reason)
        
        return {
            "id": handover_id,
            "priority": priority,
            "suggested_department": suggested_department,
            "customer_message": customer_message,
            "status": "pending"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar handover: {str(e)}")


@router.get("/", response_model=List[Dict[str, Any]])
async def list_handovers(
    status: Optional[str] = Query(None, description="Filtrar por status"),
    priority: Optional[int] = Query(None, ge=1, le=4, description="Filtrar por prioridade"),
    agent_id: Optional[str] = Query(None, description="Filtrar por agente atribuído"),
    limit: int = Query(50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """
    Lista handovers com filtros opcionais.
    
    Args:
        status: Filtrar por status (pending, accepted, in_progress, etc)
        priority: Filtrar por prioridade (1-4)
        agent_id: Filtrar por agente
        limit: Número máximo de resultados
        current_user: Usuário autenticado
        
    Returns:
        Lista de handovers
    """
    try:
        # Monta query
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        if agent_id:
            query["assigned_agent"] = agent_id
        
        # Busca handovers
        cursor = handovers_collection.find(query).sort("priority", -1).limit(limit)
        handovers = await cursor.to_list(length=limit)
        
        # Converte ObjectId para string
        for handover in handovers:
            handover["id"] = str(handover.pop("_id"))
        
        return handovers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar handovers: {str(e)}")


@router.get("/{handover_id}")
async def get_handover(
    handover_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Busca um handover específico por ID.
    
    Args:
        handover_id: ID do handover
        current_user: Usuário autenticado
        
    Returns:
        Dados do handover
    """
    try:
        handover = await handovers_collection.find_one({"_id": ObjectId(handover_id)})
        
        if not handover:
            raise HTTPException(status_code=404, detail="Handover não encontrado")
        
        handover["id"] = str(handover.pop("_id"))
        return handover
        
    except Exception as e:
        if "not a valid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="ID inválido")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar handover: {str(e)}")


@router.put("/{handover_id}/accept")
async def accept_handover(
    handover_id: str,
    request: AcceptHandoverRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Agente aceita um handover.
    
    Args:
        handover_id: ID do handover
        request: Dados do agente
        current_user: Usuário autenticado
        
    Returns:
        Handover atualizado
    """
    try:
        result = await handovers_collection.update_one(
            {"_id": ObjectId(handover_id)},
            {
                "$set": {
                    "status": HandoverStatus.accepted.value,
                    "assigned_agent": request.agent_id,
                    "assigned_agent_name": request.agent_name,
                    "accepted_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Handover não encontrado")
        
        return {"message": "Handover aceito com sucesso"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao aceitar handover: {str(e)}")


@router.put("/{handover_id}/in-progress")
async def mark_in_progress(
    handover_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Marca handover como em progresso.
    
    Args:
        handover_id: ID do handover
        current_user: Usuário autenticado
        
    Returns:
        Confirmação
    """
    try:
        result = await handovers_collection.update_one(
            {"_id": ObjectId(handover_id)},
            {"$set": {"status": HandoverStatus.in_progress.value}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Handover não encontrado")
        
        return {"message": "Status atualizado para em progresso"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar status: {str(e)}")


@router.put("/{handover_id}/resolve")
async def resolve_handover(
    handover_id: str,
    request: ResolveHandoverRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Resolve (finaliza) um handover.
    
    Args:
        handover_id: ID do handover
        request: Notas de resolução
        current_user: Usuário autenticado
        
    Returns:
        Confirmação
    """
    try:
        update_data = {
            "status": HandoverStatus.resolved.value,
            "resolved_at": datetime.utcnow()
        }
        
        if request.resolution_notes:
            update_data["resolution_notes"] = request.resolution_notes
        
        result = await handovers_collection.update_one(
            {"_id": ObjectId(handover_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Handover não encontrado")
        
        return {"message": "Handover resolvido com sucesso"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao resolver handover: {str(e)}")


@router.delete("/{handover_id}")
async def cancel_handover(
    handover_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Cancela um handover.
    
    Args:
        handover_id: ID do handover
        current_user: Usuário autenticado
        
    Returns:
        Confirmação
    """
    try:
        result = await handovers_collection.update_one(
            {"_id": ObjectId(handover_id)},
            {"$set": {"status": HandoverStatus.cancelled.value}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Handover não encontrado")
        
        return {"message": "Handover cancelado"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar handover: {str(e)}")


@router.get("/stats/summary")
async def get_handover_stats(user_id: str = Depends(get_current_user_id)):
    """
    Retorna estatísticas resumidas dos handovers.
    
    Returns:
        Contadores por status, prioridade, etc
    """
    try:
        # Total por status
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_counts = await handovers_collection.aggregate(pipeline).to_list(length=10)
        
        # Total por prioridade
        pipeline = [
            {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
        ]
        priority_counts = await handovers_collection.aggregate(pipeline).to_list(length=4)
        
        # Tempo médio de resposta (pending → accepted)
        pipeline = [
            {
                "$match": {
                    "accepted_at": {"$exists": True},
                    "created_at": {"$exists": True}
                }
            },
            {
                "$project": {
                    "response_time": {
                        "$subtract": ["$accepted_at", "$created_at"]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_response_time_ms": {"$avg": "$response_time"}
                }
            }
        ]
        avg_response = await handovers_collection.aggregate(pipeline).to_list(length=1)
        
        return {
            "by_status": {item["_id"]: item["count"] for item in status_counts},
            "by_priority": {item["_id"]: item["count"] for item in priority_counts},
            "avg_response_time_seconds": avg_response[0]["avg_response_time_ms"] / 1000 if avg_response else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar estatísticas: {str(e)}")
