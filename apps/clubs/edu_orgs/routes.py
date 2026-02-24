from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.clubs.edu_orgs.schemas import (
    EducationalOrganizationCreate,
    EducationalOrganizationResponse,
    EducationalOrganizationUpdate,
)
from apps.clubs.edu_orgs.services import EduOrgService
from apps.core.storage import upload_image_to_minio
from apps.db.dependencies import get_db

router = APIRouter(prefix="/educational-organizations", tags=["Educational organizations"])


@router.post("/", response_model=EducationalOrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_educational_organization(
    schema: EducationalOrganizationCreate,
    db: AsyncSession = Depends(get_db),
):
    return await EduOrgService.create(db, schema)


@router.get("/", response_model=list[EducationalOrganizationResponse])
async def list_educational_organizations(
    city: Optional[str] = Query(None, description="Фильтр по городу"),
    db: AsyncSession = Depends(get_db),
):
    return await EduOrgService.get_all(db, city)


@router.get("/{edu_org_id}", response_model=EducationalOrganizationResponse)
async def get_educational_organization(edu_org_id: int, db: AsyncSession = Depends(get_db)):
    edu_org = await EduOrgService.get_by_id(db, edu_org_id)
    if not edu_org:
        raise HTTPException(status_code=404, detail="Educational organization not found")
    return edu_org


@router.patch("/{edu_org_id}", response_model=EducationalOrganizationResponse)
async def update_educational_organization(
    edu_org_id: int,
    schema: EducationalOrganizationUpdate,
    db: AsyncSession = Depends(get_db),
):
    edu_org = await EduOrgService.get_by_id(db, edu_org_id)
    if not edu_org:
        raise HTTPException(status_code=404, detail="Educational organization not found")
    return await EduOrgService.update(db, edu_org, schema)


@router.delete("/{edu_org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_educational_organization(edu_org_id: int, db: AsyncSession = Depends(get_db)):
    edu_org = await EduOrgService.get_by_id(db, edu_org_id)
    if not edu_org:
        raise HTTPException(status_code=404, detail="Educational organization not found")
    await EduOrgService.delete(db, edu_org)

@router.post("/{edu_org_id}/logo", response_model=EducationalOrganizationResponse)
async def upload_educational_organization_logo(
    edu_org_id: int,
    logo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Загрузка логотипа образовательного учреждения в MinIO."""
    edu_org = await EduOrgService.get_by_id(db, edu_org_id)
    if not edu_org:
        raise HTTPException(status_code=404, detail="Educational organization not found")

    edu_org.logo_key = await upload_image_to_minio(logo, folder=f"educational-organizations/{edu_org_id}")
    await db.commit()
    await db.refresh(edu_org)
    return edu_org

