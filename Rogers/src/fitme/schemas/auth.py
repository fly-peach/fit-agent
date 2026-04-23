"""Auth Schemas"""
from pydantic import BaseModel, EmailStr


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


class LoginResponse(BaseModel):
    """登录响应"""
    code: int = 200
    data: LoginData


class LogoutResponse(BaseModel):
    """登出响应"""
    code: int = 200
    message: str = "登出成功"