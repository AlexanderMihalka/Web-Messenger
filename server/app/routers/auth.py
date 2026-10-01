"""/api/v1/auth — реєстрація, вхід, оновлення токена, вихід, поточний користувач."""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookies import clear_refresh_cookie, set_refresh_cookie
from app.core.database import get_db
from app.core.errors import UnauthorizedError
from app.core.rate_limit import client_ip, rate_limit
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserMe
from app.services.auth_service import AuthResult, AuthService
from app.services.mappers import to_user_me

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

_auth_limit = rate_limit(settings.rate_limit_auth_per_minute, 60, "auth")


def _respond_with_tokens(response: Response, result: AuthResult) -> TokenResponse:
    set_refresh_cookie(
        response, result.refresh_token, settings.refresh_token_expire_days * 24 * 3600
    )
    return TokenResponse(access_token=result.access_token, expires_in=result.expires_in)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    dependencies=[Depends(_auth_limit)],
)
def register(
    data: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    result = AuthService(db).register(data, ip=client_ip(request))
    return _respond_with_tokens(response, result)


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(_auth_limit)])
def login(
    data: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    result = AuthService(db).login(data.login, data.password, ip=client_ip(request))
    return _respond_with_tokens(response, result)


@router.post("/refresh", response_model=TokenResponse, dependencies=[Depends(_auth_limit)])
def refresh(
    request: Request,
    response: Response,
    body: RefreshRequest | None = None,
    db: Session = Depends(get_db),
) -> TokenResponse:
    raw_token = request.cookies.get("refresh_token") or (body.refresh_token if body else None)
    if not raw_token:
        raise UnauthorizedError("Відсутній refresh-токен")
    result = AuthService(db).refresh(raw_token, ip=client_ip(request))
    return _respond_with_tokens(response, result)


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    raw_token = request.cookies.get("refresh_token")
    AuthService(db).logout(raw_token, user.id)
    clear_refresh_cookie(response)


@router.get("/me", response_model=UserMe)
def me(user: User = Depends(get_current_user)) -> UserMe:
    return to_user_me(user)
