from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user
from apps.users.models import User, UserRole

from apps.core.storage import upload_image_to_minio

from apps.competitions.schemas import (
    CompetitionCreate,
    CompetitionResponse,
    CompetitionUpdate
)
from apps.competitions.services import CompetitionService
from apps.competitions.models import CompetitionStatus

router = APIRouter(prefix="/competitions", tags=["Competitions"])


@router.post("/", response_model=CompetitionResponse, status_code=status.HTTP_201_CREATED)
async def create_competition(
    schema: CompetitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать соревнование (только для Клубов).
    """
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
    """
    Публичный список соревнований.
    """
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
    """
    Обновить соревнование. Только владелец (клуб).
    """
    comp = await CompetitionService.get_by_id(db, comp_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Соревнование не найдено")

    # Проверка прав: редактировать может только создатель
    if comp.club_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не владелец этого соревнования")

    return await CompetitionService.update(db, comp_id, schema)

@router.post("/{comp_id}/photo", response_model=CompetitionResponse)
async def upload_competition_photo(
    comp_id: int,
    photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Загрузка фото для соревнования (только владелец-клуб).
    В БД сохраняется ссылка на объект в MinIO.
    """
    comp = await CompetitionService.get_by_id(db, comp_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Соревнование не найдено")

    if current_user.role != UserRole.CLUB or comp.club_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не владелец этого соревнования")

    comp.photo_key = await upload_image_to_minio(photo, folder=f"competitions/{comp_id}")
    await db.commit()
    await db.refresh(comp)
    return comp
