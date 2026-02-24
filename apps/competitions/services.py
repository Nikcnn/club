from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.competitions.models import Competition, CompetitionStatus, CompetitionSubscription
from apps.competitions.schemas import CompetitionCreate, CompetitionUpdate


class CompetitionService:
    @staticmethod
    async def cleanup_expired_competitions(db: AsyncSession) -> None:
        now = datetime.now(timezone.utc)
        await db.execute(delete(Competition).where(Competition.ends_at <= now))
        await db.commit()

    @staticmethod
    async def _ensure_no_time_overlap(
        db: AsyncSession,
        user_id: int,
        starts_at: datetime,
        ends_at: datetime,
        ignore_competition_id: Optional[int] = None,
    ) -> None:
        query = (
            select(Competition.id)
            .join(CompetitionSubscription, CompetitionSubscription.competition_id == Competition.id)
            .where(CompetitionSubscription.user_id == user_id)
            .where(Competition.starts_at < ends_at)
            .where(Competition.ends_at > starts_at)
        )
        if ignore_competition_id is not None:
            query = query.where(Competition.id != ignore_competition_id)

        overlap = (await db.execute(query)).scalar_one_or_none()
        if overlap is not None:
            raise ValueError("Время соревнования пересекается с уже отслеживаемым")

    @staticmethod
    async def create(
        db: AsyncSession,
        schema: CompetitionCreate,
        club_id: int
    ) -> Competition:
        now = datetime.now(timezone.utc)
        if schema.ends_at <= now:
            raise ValueError("Нельзя создать уже завершенное соревнование")

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
        await CompetitionService.cleanup_expired_competitions(db)
        query = select(Competition)

        if status:
            query = query.where(Competition.status == status)

        if club_id:
            query = query.where(Competition.club_id == club_id)

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
        new_starts_at = update_data.get("starts_at", comp.starts_at)
        new_ends_at = update_data.get("ends_at", comp.ends_at)

        if new_ends_at <= new_starts_at:
            raise ValueError("Дата окончания должна быть позже даты начала")
        if new_ends_at <= datetime.now(timezone.utc):
            raise ValueError("Нельзя обновить соревнование в прошедшее время")

        subscription_users = await db.execute(
            select(CompetitionSubscription.user_id).where(CompetitionSubscription.competition_id == comp.id)
        )
        for user_id in subscription_users.scalars().all():
            await CompetitionService._ensure_no_time_overlap(
                db,
                user_id=user_id,
                starts_at=new_starts_at,
                ends_at=new_ends_at,
                ignore_competition_id=comp.id,
            )

        for key, value in update_data.items():
            setattr(comp, key, value)

        await db.commit()
        await db.refresh(comp)
        return comp

    @staticmethod
    async def subscribe_user(db: AsyncSession, comp_id: int, user_id: int) -> CompetitionSubscription:
        competition = await CompetitionService.get_by_id(db, comp_id)
        if not competition:
            raise ValueError("Соревнование не найдено")
        if competition.ends_at <= datetime.now(timezone.utc):
            await db.delete(competition)
            await db.commit()
            raise ValueError("Соревнование уже завершено")

        existing = await db.execute(
            select(CompetitionSubscription).where(
                and_(
                    CompetitionSubscription.competition_id == comp_id,
                    CompetitionSubscription.user_id == user_id,
                )
            )
        )
        subscription = existing.scalar_one_or_none()
        if subscription:
            return subscription

        await CompetitionService._ensure_no_time_overlap(
            db,
            user_id=user_id,
            starts_at=competition.starts_at,
            ends_at=competition.ends_at,
        )

        subscription = CompetitionSubscription(competition_id=comp_id, user_id=user_id)
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        return subscription

    @staticmethod
    async def unsubscribe_user(db: AsyncSession, comp_id: int, user_id: int) -> bool:
        sub = await db.execute(
            select(CompetitionSubscription).where(
                and_(
                    CompetitionSubscription.competition_id == comp_id,
                    CompetitionSubscription.user_id == user_id,
                )
            )
        )
        subscription = sub.scalar_one_or_none()
        if not subscription:
            return False

        await db.delete(subscription)
        await db.commit()
        return True
