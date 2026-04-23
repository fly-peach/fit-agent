"""Common Schemas"""
from pydantic import BaseModel
from typing import Optional, Any


class BaseResponse(BaseModel):
    """通用响应格式"""
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int
    message: str
    data: Optional[Any] = None