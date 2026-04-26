# SSE response format helpers for AgentScopeRuntimeWebUI compatibility
import json
import uuid
import time
from typing import Optional, List, Any


def format_sse_event(data: dict) -> str:
    """Format a JSON object as an SSE event."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def generate_uuid(prefix: str = "") -> str:
    """Generate a UUID with optional prefix."""
    return f"{prefix}{uuid.uuid4().hex}"


def create_response_event(
    response_id: str,
    status: str,
    created_at: Optional[int] = None,
    output: Optional[List[Any]] = None,
) -> dict:
    """Create a response object event."""
    return {
        "sequence_number": 0,
        "object": "response",
        "status": status,
        "error": None,
        "id": response_id,
        "created_at": created_at or int(time.time()),
        "completed_at": None if status != "completed" else int(time.time()),
        "output": output,
        "usage": None,
        "session_id": None,
    }


def create_message_event(
    msg_id: str,
    status: str,
    role: str = "assistant",
    content: Optional[List[Any]] = None,
    msg_type: str = "message",
) -> dict:
    """Create a message object event."""
    return {
        "sequence_number": 0,
        "object": "message",
        "status": status,
        "error": None,
        "id": msg_id,
        "type": msg_type,
        "role": role,
        "content": content,
        "code": None,
        "message": None,
        "usage": None,
        "metadata": None,
    }


def create_content_chunk(
    msg_id: str,
    text: str,
    index: int = 0,
    delta: bool = True,
) -> dict:
    """Create a content chunk event for streaming."""
    return {
        "sequence_number": 0,
        "object": "content",
        "status": "in_progress",
        "error": None,
        "type": "text",
        "index": index,
        "delta": delta,
        "msg_id": msg_id,
        "text": text,
    }


def create_completed_content(text: str) -> dict:
    """Create a completed content object."""
    return {
        "sequence_number": 0,
        "object": "content",
        "status": "completed",
        "error": None,
        "type": "text",
        "index": None,
        "delta": None,
        "msg_id": None,
        "text": text,
    }