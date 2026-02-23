from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.storage import upload_image_to_minio
from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user
from apps.users.models import User, UserRole
from apps.users.services import UserService  # Для проверки уникальности email

from apps.organizations.schemas import OrganizationCreate, OrganizationResponse, OrganizationUpdate
from apps.organizations.services import OrganizationService
from apps.organizations.models import Organization

router = APIRouter(prefix="/organizations", tags=["Organizations"])


# === PUBLIC ===

@router.post("/register", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def register_organization(
    schema: OrganizationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация организатора соревнований.
    """
    # Проверяем email
    if await UserService.get_by_email(db, schema.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    return await OrganizationService.create(db, schema)


@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(
    city: Optional[str] = Query(None, description="Фильтр по городу"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Каталог организаций.
    """
    return await OrganizationService.get_all(db, city, search, skip, limit)


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization_profile(
    org_id: int,
    db: AsyncSession = Depends(get_db)
):
    org = await OrganizationService.get_by_id(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


# === PROTECTED ===

@router.patch("/me", response_model=OrganizationResponse)
async def update_my_organization(
    schema: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Редактирование своего профиля (только для ROLE_ORGANIZATION).
    """
    if current_user.role != UserRole.ORGANIZATION:
        raise HTTPException(status_code=403, detail="Only organizations can edit this profile")

    # Подгружаем именно Organization модель
    org = await OrganizationService.get_by_id(db, current_user.id)

    return await OrganizationService.update(db, org, schema)


@router.post("/me/logo", response_model=OrganizationResponse)
async def upload_my_logo(
    logo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Загрузка логотипа организации в MinIO с сохранением ключа в профиле."""
    if current_user.role != UserRole.ORGANIZATION:
        raise HTTPException(status_code=403, detail="Only organizations can upload logo")

    org = await OrganizationService.get_by_id(db, current_user.id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.logo_key = await upload_image_to_minio(logo, folder=f"organizations/{current_user.id}")
    await db.commit()
    await db.refresh(org)
    return org
