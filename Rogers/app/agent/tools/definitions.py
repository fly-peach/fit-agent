from __future__ import annotations

from app.agent.tools.multimodal import analyze_food_image, analyze_scale_image
from app.agent.tools.read_tools import get_health_metrics, analyze_body_composition


def list_read_tools() -> list:
    return [get_health_metrics, analyze_body_composition]


def list_multimodal_tools() -> list:
    return [analyze_food_image, analyze_scale_image]
