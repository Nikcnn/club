from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.competitions.models import CompetitionStatus
from apps.competitions.schemas import (
    CompetitionCreate,
    CompetitionResponse,
    CompetitionSubscriptionResponse,
    CompetitionUpdate,
)
from apps.competitions.services import CompetitionService
from apps.core.storage import upload_image_to_minio
from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user
from apps.users.models import User, UserRole

router = APIRouter(prefix="/competitions", tags=["Competitions"])


@router.post("/", response_model=CompetitionResponse, status_code=status.HTTP_201_CREATED)
async def create_competition(
    schema: CompetitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.CLUB:
        raise HTTPException(status_code=403, detail="Только клубы могут создавать соревнования")

    return await CompetitionService.create(db, schema, club_id=current_user.id)


@router.get("/", response_model=List[CompetitionResponse])
async def list_competitions(
    status: Optional[CompetitionStatus] = Query(None, description="Фильтр по статусу"),
    club_id: Optional[int] = Query(None, description="Фильтр по клубу"),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    return await CompetitionService.get_all(db, skip, limit, status, club_id)


@router.get("/{comp_id}", response_model=CompetitionResponse)
async def get_competition(
    comp_id: int,
    db: AsyncSession = Depends(get_db)
):
    comp = await CompetitionService.get_by_id(db, comp_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Соревнование не найдено")
    return comp


@router.patch("/{comp_id}", response_model=CompetitionResponse)
async def update_competition(
    comp_id: int,
    schema: CompetitionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comp = await CompetitionService.get_by_id(db, comp_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Соревнование не найдено")

    if comp.club_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не владелец этого соревнования")

    try:
        return await CompetitionService.update(db, comp_id, schema)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{comp_id}/photo", response_model=CompetitionResponse)
async def upload_competition_photo(
    comp_id: int,
    photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comp = await CompetitionService.get_by_id(db, comp_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Соревнование не найдено")

    if current_user.role != UserRole.CLUB or comp.club_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не владелец этого соревнования")

    comp.photo_key = await upload_image_to_minio(photo, folder=f"competitions/{comp_id}")
    await db.commit()
    await db.refresh(comp)
    return comp


@router.post("/{comp_id}/subscribe", response_model=CompetitionSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def subscribe_to_competition(
    comp_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await CompetitionService.subscribe_user(db, comp_id=comp_id, user_id=current_user.id)
    except ValueError as exc:
        detail = str(exc)
        code = 404 if detail == "Соревнование не найдено" else 400
        raise HTTPException(status_code=code, detail=detail) from exc


@router.delete("/{comp_id}/subscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_from_competition(
    comp_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    removed = await CompetitionService.unsubscribe_user(db, comp_id=comp_id, user_id=current_user.id)
    if not removed:
        raise HTTPException(status_code=404, detail="Подписка не найдена")
    return None
