from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.clubs.edu_orgs.models import EducationalOrganization
from apps.clubs.edu_orgs.schemas import EducationalOrganizationCreate, EducationalOrganizationUpdate


class EduOrgService:
    @staticmethod
    async def create(db: AsyncSession, schema: EducationalOrganizationCreate) -> EducationalOrganization:
        edu_org = EducationalOrganization(**schema.model_dump())
        db.add(edu_org)
        await db.commit()
        await db.refresh(edu_org)
        return edu_org

    @staticmethod
    async def get_all(db: AsyncSession, city: Optional[str] = None) -> list[EducationalOrganization]:
        query = select(EducationalOrganization)
        if city:
            query = query.where(EducationalOrganization.city == city)

        result = await db.execute(query.order_by(EducationalOrganization.name.asc()))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, edu_org_id: int) -> Optional[EducationalOrganization]:
        result = await db.execute(select(EducationalOrganization).where(EducationalOrganization.id == edu_org_id))
        return result.scalars().first()

    @staticmethod
    async def update(
        db: AsyncSession,
        edu_org: EducationalOrganization,
        schema: EducationalOrganizationUpdate,
    ) -> EducationalOrganization:
        for key, value in schema.model_dump(exclude_unset=True).items():
            setattr(edu_org, key, value)

        await db.commit()
        await db.refresh(edu_org)
        return edu_org

    @staticmethod
    async def delete(db: AsyncSession, edu_org: EducationalOrganization) -> None:
        await db.delete(edu_org)
        await db.commit()
