from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from apps.clubs.edu_orgs.models import Educat
from apps.clubs.edu_orgs.schemas import EducationalOrganizationBase, EducationalOrganizationUpdate


class EduOrgService:
    @staticmethod
    async def create(
        db: AsyncSession,
        schema: EducationalOrganizationBase,
    ) -> Educat:
        edu = Educat(
            **schema.model_dump(),
        )
        db.add(edu)
        await db.commit()
        await db.refresh(edu)
        return edu
    @staticmethod
    async def update(
        db: AsyncSession,
        schema: EducationalOrganizationUpdate
    ) -> Optional[Educat]:
        edu = Educat(
            **schema.model_dump(exclude_unset=True),
        )
        db.add(edu)
        await db.commit()
        await db.refresh(edu)
        return edu