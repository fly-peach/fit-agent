# -*- coding: utf-8 -*-
"""Multimodal tools: image loading and analysis for the AI coach agent."""

from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
import os
import re
import unicodedata
from pathlib import Path
from typing import Optional

from agentscope.message import ImageBlock, TextBlock
from agentscope.tool import ToolResponse

from app.core.config import settings

# ---------------------------------------------------------------------------
# Media path validation
# ---------------------------------------------------------------------------

_IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif",
}


def _validate_media_path(
    file_path: str,
    allowed_extensions: set[str],
    mime_prefix: str,
) -> tuple[Path, Optional[ToolResponse]]:
    """Validate a media file path.

    Returns ``(resolved_path, None)`` on success or
    ``(_, error_response)`` on failure.
    """
    file_path = unicodedata.normalize("NFC", os.path.expanduser(file_path))
    resolved = Path(file_path).resolve()

    if not resolved.exists() or not resolved.is_file():
        return resolved, ToolResponse(
            content=[TextBlock(type="text", text=f"Error: {file_path} does not exist or is not a file.")],
        )

    ext = resolved.suffix.lower()
    mime, _ = mimetypes.guess_type(str(resolved))
    if ext not in allowed_extensions and (not mime or not mime.startswith(f"{mime_prefix}/")):
        return resolved, ToolResponse(
            content=[TextBlock(type="text", text=f"Error: {resolved.name} is not a supported {mime_prefix} format.")],
        )

    return resolved, None


# ---------------------------------------------------------------------------
# Image viewing tools (load image into LLM context)
# ---------------------------------------------------------------------------

async def view_image(image_path: str) -> ToolResponse:
    """Load a local image file into the LLM context for inspection.

    Args:
        image_path: Path to the image file.

    Returns:
        An ImageBlock the model can inspect, or an error message.
    """
    resolved, err = _validate_media_path(image_path, _IMAGE_EXTENSIONS, "image")
    if err is not None:
        return err

    return ToolResponse(
        content=[
            ImageBlock(type="image", source={"type": "url", "url": str(resolved)}),
            TextBlock(type="text", text=f"Image loaded: {resolved.name}"),
        ],
    )


async def view_image_base64(image_base64: str, mime_type: str = "image/jpeg") -> ToolResponse:
    """Load a base64-encoded image into the LLM context.

    Args:
        image_base64: Base64-encoded image data.
        mime_type: MIME type of the image. Defaults to "image/jpeg".

    Returns:
        An ImageBlock the model can inspect.
    """
    data_url = f"data:{mime_type};base64,{image_base64}"
    return ToolResponse(
        content=[
            ImageBlock(type="image", source={"type": "url", "url": data_url}),
            TextBlock(type="text", text="Image loaded from base64 data."),
        ],
    )


# ---------------------------------------------------------------------------
# Image analysis tools (call LLM and return structured JSON)
# ---------------------------------------------------------------------------

def _safe_parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except Exception:
            return {}


def _get_multimodal_model():
    if not settings.dashscope_coding_api_key:
        return None
    try:
        from agentscope.model import DashScopeChatModel
        return DashScopeChatModel(
            model_name=settings.model,
            api_key=settings.dashscope_coding_api_key,
            stream=False,
            enable_thinking=False,
        )
    except Exception:
        return None


def analyze_food_image(*, image_path: str = "", image_base64: str = "") -> dict:
    """Analyze a food image and return estimated nutrition data.

    Accepts either a local file path or base64-encoded image data.

    Returns:
        Dict with food_name, portion, calories_kcal, protein_g, carb_g, fat_g, confidence.
    """
    if image_path:
        resolved, err = _validate_media_path(image_path, _IMAGE_EXTENSIONS, "image")
        if err is not None:
            return {"error": f"Invalid image path: {image_path}"}
        with open(resolved, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()

    model = _get_multimodal_model()
    if model is None:
        return {
            "food_name": "未知食物", "portion": "未知份量",
            "calories_kcal": 0, "protein_g": 0, "carb_g": 0, "fat_g": 0,
            "confidence": "low", "note": "LLM 未配置完成，无法进行图片识别",
        }

    async def _run() -> dict:
        from agentscope.message import Msg

        msg = Msg(
            name="user",
            role="user",
            content=[
                {"type": "text", "text": (
                    "请识别这张食物图片，并只返回 JSON，字段必须包含："
                    "food_name, portion, calories_kcal, protein_g, carb_g, fat_g, confidence"
                )},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ],
        )
        resp = await model([msg])
        content = getattr(resp, "content", "")
        parsed = _safe_parse_json(str(content))
        return {
            "food_name": parsed.get("food_name", "未知食物"),
            "portion": parsed.get("portion", "未知份量"),
            "calories_kcal": parsed.get("calories_kcal", 0),
            "protein_g": parsed.get("protein_g", 0),
            "carb_g": parsed.get("carb_g", 0),
            "fat_g": parsed.get("fat_g", 0),
            "confidence": parsed.get("confidence", "estimated"),
        }

    try:
        return asyncio.run(_run())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()
    except Exception:
        return {
            "food_name": "未知食物", "portion": "未知份量",
            "calories_kcal": 0, "protein_g": 0, "carb_g": 0, "fat_g": 0,
            "confidence": "low", "note": "图片识别失败",
        }


def analyze_scale_image(*, image_path: str = "", image_base64: str = "") -> dict:
    """Analyze a weight scale image and return the reading.

    Accepts either a local file path or base64-encoded image data.

    Returns:
        Dict with weight, unit, confidence.
    """
    if image_path:
        resolved, err = _validate_media_path(image_path, _IMAGE_EXTENSIONS, "image")
        if err is not None:
            return {"error": f"Invalid image path: {image_path}"}
        with open(resolved, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()

    model = _get_multimodal_model()
    if model is None:
        return {
            "weight": None, "unit": "kg",
            "confidence": "low", "note": "LLM 未配置完成，无法进行体重秤识别",
        }

    async def _run() -> dict:
        from agentscope.message import Msg

        msg = Msg(
            name="user",
            role="user",
            content=[
                {"type": "text", "text": "请识别体重秤图片上的读数，只返回 JSON：weight, unit, confidence"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ],
        )
        resp = await model([msg])
        content = getattr(resp, "content", "")
        parsed = _safe_parse_json(str(content))
        return {
            "weight": parsed.get("weight"),
            "unit": parsed.get("unit", "kg"),
            "confidence": parsed.get("confidence", "estimated"),
        }

    try:
        return asyncio.run(_run())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()
    except Exception:
        return {
            "weight": None, "unit": "kg",
            "confidence": "low", "note": "体重秤识别失败",
        }
