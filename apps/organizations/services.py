from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from apps.organizations.models import Organization
from apps.organizations.schemas import OrganizationCreate, OrganizationUpdate
from apps.users.models import UserRole
from apps.users.utils import get_password_hash  # Импортируем утилиту хеширования


class OrganizationService:
    @staticmethod
    async def create(db: AsyncSession, schema: OrganizationCreate) -> Organization:
        # 1. Хешируем пароль
        hashed_pw = get_password_hash(schema.password)

        # 2. Создаем организацию
        org = Organization(
            email=schema.email,
            hashed_password=hashed_pw,
            role=UserRole.ORGANIZATION,
            is_active=True,
            name=schema.name,
            city=schema.city,
            description=schema.description,
            website=schema.website,
            logo_key=schema.logo_key
        )

        db.add(org)
        await db.commit()
        await db.refresh(org)
        return org

    @staticmethod
    async def get_by_id(db: AsyncSession, org_id: int) -> Optional[Organization]:
        query = select(Organization).where(Organization.id == org_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        city: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Organization]:
        query = select(Organization)

        if city:
            query = query.where(Organization.city == city)

        if search:
            query = query.where(
                or_(
                    Organization.name.ilike(f"%{search}%"),
                    Organization.description.ilike(f"%{search}%")
                )
            )

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update(
        db: AsyncSession,
        org: Organization,
        schema: OrganizationUpdate
    ) -> Organization:
        update_data = schema.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(org, key, value)

        await db.commit()
        await db.refresh(org)
        return org