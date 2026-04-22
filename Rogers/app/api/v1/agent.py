from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agent.schemas.agent import AgentApproveRequest, AgentChatRequest
from app.agent.service.agent_service import AgentService
from app.api.deps import get_current_user, get_db
from app.models.user import User

router = APIRouter()


@router.post("/chat", response_model=dict[str, Any])
def chat_with_agent(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payload: AgentChatRequest,
) -> Any:
    service = AgentService(db)
    data = service.chat(current_user=current_user, payload=payload)
    return {"code": 0, "message": "success", "data": data.model_dump()}


@router.get("/pending", response_model=dict[str, Any])
def list_pending_actions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    service = AgentService(db)
    data = service.list_pending(current_user=current_user)
    return {"code": 0, "message": "success", "data": [x.model_dump() for x in data]}


@router.post("/approve", response_model=dict[str, Any])
def approve_action(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payload: AgentApproveRequest,
) -> Any:
    service = AgentService(db)
    data = service.approve(current_user=current_user, payload=payload)
    return {"code": 0, "message": "success", "data": data.model_dump()}


@router.get("/history", response_model=dict[str, Any])
def list_agent_history(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: str = Query(...),
    format: str = Query("plain"),
) -> Any:
    service = AgentService(db)
    data = service.list_history(current_user=current_user, session_id=session_id, format=format)
    return {"code": 0, "message": "success", "data": data}


@router.get("/sessions", response_model=dict[str, Any])
def list_agent_sessions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    service = AgentService(db)
    data = service.list_sessions(current_user=current_user)
    return {"code": 0, "message": "success", "data": data}


@router.delete("/sessions/{session_id}", response_model=dict[str, Any])
def delete_agent_session(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: str,
) -> Any:
    service = AgentService(db)
    deleted = service.delete_session(current_user=current_user, session_id=session_id)
    return {"code": 0, "message": "success", "data": {"deleted": deleted}}


@router.post("/chat/stream")
def chat_with_agent_stream(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payload: AgentChatRequest,
    reconnect: bool = Query(False),
    run_id: str | None = Query(None),
    last_seq: int = Query(0, ge=0),
    protocol: str = Query("modern"),
):
    service = AgentService(db)
    generator = service.chat_stream(
        current_user=current_user,
        payload=payload,
        reconnect=reconnect,
        run_id=run_id,
        last_seq=last_seq,
        protocol=protocol,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/compression/status", response_model=dict[str, Any])
def get_compression_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: str = Query(...),
) -> Any:
    service = AgentService(db)
    data = service.compression_status(current_user=current_user, session_id=session_id)
    return {"code": 0, "message": "success", "data": data}


@router.get("/compression/events", response_model=dict[str, Any])
def list_compression_events(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: str = Query(...),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    service = AgentService(db)
    data = service.compression_events(current_user=current_user, session_id=session_id, limit=limit)
    return {"code": 0, "message": "success", "data": data}


@router.get("/history/original", response_model=dict[str, Any])
def get_original_history(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: str = Query(...),
) -> Any:
    service = AgentService(db)
    data = service.original_history(current_user=current_user, session_id=session_id)
    return {"code": 0, "message": "success", "data": data}


@router.get("/offload/{offload_id}", response_model=dict[str, Any])
def get_offload_content(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    offload_id: str,
) -> Any:
    service = AgentService(db)
    try:
        data = service.load_offload_content(current_user=current_user, offload_id=offload_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"code": 0, "message": "success", "data": data}
