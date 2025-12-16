from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from deps import get_current_user_id

router = APIRouter(prefix="/custom-bots", tags=["custom-bots"])


class CustomBotCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    emoji: str = Field(default="🤖", max_length=4)
    prompt: str = Field(..., min_length=50)
    specialties: list[str] = Field(default_factory=list, max_length=5)
    openaiApiKey: str = Field(..., min_length=20, alias="openaiApiKey")
    openaiAccount: Optional[str] = Field(default=None, alias="openaiAccount")


@router.post("")
async def create_custom_bot(body: CustomBotCreate, current_user_id: str = Depends(get_current_user_id)):
    from bots.agents import create_custom_agent
    agent = await create_custom_agent(
        user_id=current_user_id,
        name=body.name,
        emoji=body.emoji,
        system_prompt=body.prompt,
        specialties=body.specialties,
        openai_api_key=body.openaiApiKey,
        openai_account=body.openaiAccount
    )
    return {
        "success": True,
        "bot": {
            "name": agent.name,
            "emoji": agent.emoji,
            "key": agent.name.lower().replace(' ', ''),
            "specialties": agent.specialties,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
    }


@router.get("")
async def list_custom_bots(current_user_id: str = Depends(get_current_user_id)):
    from bots.agents import list_custom_agents
    agents = await list_custom_agents(current_user_id)
    return {
        "bots": [
            {
                "name": agent.name,
                "emoji": agent.emoji,
                "key": agent.name.lower().replace(' ', ''),
                "specialties": agent.specialties
            }
            for agent in agents
        ]
    }


@router.delete("/{bot_key}")
async def delete_custom_bot(bot_key: str, current_user_id: str = Depends(get_current_user_id)):
    from bots.agents import delete_custom_agent
    success = await delete_custom_agent(current_user_id, bot_key)
    if not success:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    return {"success": True, "message": "Bot deletado com sucesso"}
