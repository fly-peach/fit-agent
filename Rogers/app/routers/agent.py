"""Agent Router"""
import sys
import os

sys.path.insert(0, "E:/fitagent/rogers/src")

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from pydantic import BaseModel

from src.fitme.services.auth_service import AuthService
from src.fitme.utils.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/agent", tags=["Agent"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    is_last: bool = False


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get current user from token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    user = AuthService.get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Token expired")
    return user


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with AI assistant"""
    import uuid
    session_id = request.session_id or str(uuid.uuid4())

    # TODO: Integrate with AgentScope agent
    # For now, return a placeholder response
    return ChatResponse(
        session_id=session_id,
        message="AI assistant placeholder - agent integration pending",
        is_last=True,
    )


@router.get("/sessions")
async def list_sessions(
    current_user=Depends(get_current_user)
):
    """List user sessions"""
    return {"sessions": []}
