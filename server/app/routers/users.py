"""/api/v1/users — профіль, пошук, список, блокування."""

from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.common import Page
from app.schemas.user import UserMe, UserPublic, UserUpdate
from app.services.avatar_service import save_avatar
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("", response_model=Page[UserPublic])
def list_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[UserPublic]:
    return UserService(db).list_public(user.id, limit, offset)


@router.get("/search", response_model=list[UserPublic])
def search_users(
    q: str = Query(..., min_length=1, max_length=64),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserPublic]:
    return UserService(db).search(user.id, q)


@router.get("/me/blocked", response_model=list[UserPublic])
def list_blocked(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[UserPublic]:
    return UserService(db).list_blocked(user)


@router.patch("/me", response_model=UserMe)
def update_me(
    data: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserMe:
    return UserService(db).update_me(user, data)


@router.post("/me/avatar", response_model=UserMe)
async def upload_avatar(
    file: UploadFile, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserMe:
    raw = await file.read()
    avatar_url = save_avatar(user.id, raw)
    return UserService(db).set_avatar_url(user, avatar_url)


@router.get("/{user_id}", response_model=UserPublic)
def get_user(
    user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserPublic:
    return UserService(db).get_public(user_id)


@router.post("/{user_id}/block", response_model=UserPublic, status_code=201)
def block_user(
    user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserPublic:
    service = UserService(db)
    service.block(user, user_id)
    return service.get_public(user_id)


@router.delete("/{user_id}/block", response_model=UserPublic)
def unblock_user(
    user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserPublic:
    service = UserService(db)
    service.unblock(user, user_id)
    return service.get_public(user_id)
