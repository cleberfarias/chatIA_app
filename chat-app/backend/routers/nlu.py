"""
Rotas para análise de NLU (Natural Language Understanding).

Endpoints para detectar intenções e extrair entidades de textos.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

from bots.nlu import detect_intent, requires_human_handover, suggest_response_template
from bots.entities import extract_entities
from database import interactions_collection
from deps import get_current_user_id

router = APIRouter(prefix="/nlu", tags=["NLU"])


class AnalyzeRequest(BaseModel):
    """Request para análise de texto"""
    text: str
    speaker: str = "customer"  # "customer" ou "agent"
    context: Optional[Dict[str, Any]] = None


class AnalyzeResponse(BaseModel):
    """Response com análise de NLU"""
    intent: str
    confidence: float
    entities: Dict[str, Any]
    requires_handover: bool
    suggested_response: Optional[str] = None


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(
    request: AnalyzeRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Analisa um texto para detectar intenção e extrair entidades.
    
    Args:
        request: Texto e contexto para análise
        current_user: Usuário autenticado
        
    Returns:
        Intent detectado, entities extraídas, e sugestões
    """
    try:
        # Detecta intenção (agora é async)
        intent = await detect_intent(request.text, request.speaker)
        
        # Extrai entidades
        entities = extract_entities(request.text, request.context or {})
        
        # Verifica se precisa handover
        needs_handover = requires_human_handover(intent)
        
        # Sugere resposta (se aplicável)
        suggested = None
        if intent.name != "unknown":
            suggested = suggest_response_template(intent)
        
        # Registra interação (opcional, para análise futura)
        await interactions_collection.insert_one({
            "user_id": user_id,
            "question": request.text,
            "intent": intent.name,
            "intent_confidence": intent.confidence,
            "entities": {k: v.dict() for k, v in entities.items()},
            "timestamp": datetime.utcnow()
        })
        
        return AnalyzeResponse(
            intent=intent.name,
            confidence=intent.confidence,
            entities={k: v.dict() for k, v in entities.items()},
            requires_handover=needs_handover,
            suggested_response=suggested
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao analisar texto: {str(e)}")


@router.get("/intents")
async def list_intents(speaker: str = "customer"):
    """
    Lista todas as intenções disponíveis.
    
    Args:
        speaker: "customer" ou "agent"
        
    Returns:
        Lista de intenções com descrições
    """
    from bots.nlu import CUSTOMER_INTENTS, AGENT_INTENTS
    
    intents_map = CUSTOMER_INTENTS if speaker == "customer" else AGENT_INTENTS
    
    return {
        "speaker": speaker,
        "intents": [
            {
                "name": name,
                "keywords": data["keywords"],
                "description": data.get("description", "")
            }
            for name, data in intents_map.items()
        ]
    }


@router.post("/extract-entities")
async def extract_entities_endpoint(request: AnalyzeRequest):
    """
    Extrai apenas entidades de um texto (sem análise de intent).
    
    Args:
        request: Texto e contexto
        
    Returns:
        Entidades extraídas
    """
    try:
        entities = extract_entities(request.text, request.context or {})
        
        return {
            "entities": {k: v.dict() for k, v in entities.items()},
            "count": len(entities)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao extrair entidades: {str(e)}")
