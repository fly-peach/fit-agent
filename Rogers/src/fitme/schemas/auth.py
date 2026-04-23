"""Auth Schemas"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str


class UserInfo(BaseModel):
    """用户信息"""
    userId: int
    name: str
    email: EmailStr
    role: str


class LoginData(BaseModel):
    """登录数据"""
    token: str
    user: UserInfo


class RegisterRequest(BaseModel):
    """注册请求"""
    name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class RegisterResponse(BaseModel):
    """注册响应"""
    code: int = 200
    message: str = "注册成功"
    data: LoginData


class LoginResponse(BaseModel):
    """登录响应"""
    code: int = 200
    data: LoginData


class LogoutResponse(BaseModel):
    """登出响应"""
    code: int = 200
    message: str = "登出成功"