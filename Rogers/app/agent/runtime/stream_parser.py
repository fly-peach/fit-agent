from __future__ import annotations

import json
from typing import Any


def format_sse_event(event: str, data: dict[str, Any]) -> str:
    """
    Build a SSE frame with stable JSON encoding.
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
