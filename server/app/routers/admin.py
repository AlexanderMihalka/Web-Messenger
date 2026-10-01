"""/api/v1/admin — керування користувачами, статистика, журнали подій."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.permissions import require_admin
from app.models import User
from app.schemas.admin import AdminUserOut, BlockRequest, LogOut, StatisticsOut
from app.schemas.common import Page
from app.services.admin_service import AdminService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/users", response_model=Page[AdminUserOut])
def list_users(
    q: str | None = Query(None, max_length=64),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Page[AdminUserOut]:
    return AdminService(db).list_users(q, limit, offset)


@router.get("/statistics", response_model=StatisticsOut)
def statistics(_admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> StatisticsOut:
    return AdminService(db).statistics()


@router.get("/logs", response_model=Page[LogOut])
def logs(
    level: str | None = Query(None, max_length=16),
    event: str | None = Query(None, max_length=64),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Page[LogOut]:
    return AdminService(db).get_logs(level, event, limit, offset)


@router.patch("/users/{user_id}/block", response_model=AdminUserOut)
def set_user_blocked(
    user_id: int,
    data: BlockRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserOut:
    return AdminService(db).set_blocked(admin, user_id, data.blocked)


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)
) -> None:
    AdminService(db).delete_user(admin, user_id)
