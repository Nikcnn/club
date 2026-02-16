from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from apps.competitions.models import Competition, CompetitionStatus
from apps.competitions.schemas import CompetitionCreate, CompetitionUpdate


class CompetitionService:
    @staticmethod
    async def create(
        db: AsyncSession,
        schema: CompetitionCreate,
        club_id: int
    ) -> Competition:
        comp = Competition(
            **schema.model_dump(),
            club_id=club_id,
            status=CompetitionStatus.DRAFT
        )
        db.add(comp)
        await db.commit()
        await db.refresh(comp)
        return comp

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status: Optional[CompetitionStatus] = None,
        club_id: Optional[int] = None
    ) -> List[Competition]:
        query = select(Competition)

        if status:
            query = query.where(Competition.status == status)

        if club_id:
            query = query.where(Competition.club_id == club_id)

        # Сортировка: сначала ближайшие по дате начала
        query = query.order_by(desc(Competition.starts_at)).offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, comp_id: int) -> Optional[Competition]:
        query = select(Competition).where(Competition.id == comp_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession,
        comp_id: int,
        schema: CompetitionUpdate
    ) -> Optional[Competition]:
        comp = await CompetitionService.get_by_id(db, comp_id)
        if not comp:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(comp, key, value)

        await db.commit()
        await db.refresh(comp)
        return comp