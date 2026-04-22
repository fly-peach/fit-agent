from fastapi import APIRouter, Depends

from app.api.deps import get_auth_service, get_current_user
from app.schemas.auth import AuthTokenResponse, LoginRequest, RefreshTokenRequest, RegisterRequest, RegisterResponse
from app.schemas.user import UserPublic
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse)
def register(payload: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.register(payload)


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.login(payload)


@router.post("/refresh", response_model=AuthTokenResponse)
def refresh(payload: RefreshTokenRequest, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.refresh(payload)


@router.get("/me", response_model=UserPublic)
def me(current_user=Depends(get_current_user)):
    return current_user
