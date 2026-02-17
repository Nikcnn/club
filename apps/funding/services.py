from typing import List, Optional
from decimal import Decimal

# Импортируем функции SQL
from sqlalchemy import select, desc, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from apps.funding.models import Campaign, Investment, CampaignStatus, InvestmentStatus
from apps.funding.schemas import CampaignCreate, CampaignUpdate, InvestmentCreate


class CampaignService:
    @staticmethod
    async def create(db: AsyncSession, schema: CampaignCreate, club_id: int) -> Campaign:
        campaign = Campaign(
            **schema.model_dump(),
            club_id=club_id,
            status=CampaignStatus.DRAFT
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        return campaign

    @staticmethod
    async def get_all(
        db: AsyncSession,
        club_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Campaign]:
        # 1. Формируем запрос: выбираем Саму Кампанию И Сумму её инвестиций
        # func.coalesce(..., 0) превращает NULL в 0, если инвестиций нет
        query = select(
            Campaign,
            func.coalesce(func.sum(Investment.amount), 0).label("current_amount")
        )

        # 2. Джойним таблицу инвестиций.
        # Важно: фильтруем только ОПЛАЧЕННЫЕ (PAID) инвестиции прямо в джойне.
        query = query.outerjoin(
            Investment,
            and_(
                Investment.campaign_id == Campaign.id,
                Investment.status == InvestmentStatus.PAID
            )
        )

        # 3. Фильтры
        if club_id:
            query = query.where(Campaign.club_id == club_id)

        # 4. Группировка (обязательна при агрегации) и сортировка
        query = query.group_by(Campaign.id)
        query = query.order_by(desc(Campaign.created_at)).offset(skip).limit(limit)

        result = await db.execute(query)

        # 5. Обработка результата
        # result.all() вернет список кортежей: [(CampaignObj, 1500.00), (CampaignObj, 0), ...]
        campaigns_data = result.all()

        campaigns = []
        for campaign, amount in campaigns_data:
            # Трюк: динамически добавляем атрибут current_amount в объект модели.
            # Pydantic (from_attributes=True) увидит это поле при сериализации.
            campaign.current_amount = amount
            campaigns.append(campaign)

        return campaigns

    @staticmethod
    async def get_by_id(db: AsyncSession, campaign_id: int) -> Optional[Campaign]:
        # То же самое для одной кампании
        query = select(
            Campaign,
            func.coalesce(func.sum(Investment.amount), 0).label("current_amount")
        ).outerjoin(
            Investment,
            and_(
                Investment.campaign_id == Campaign.id,
                Investment.status == InvestmentStatus.PAID
            )
        ).where(Campaign.id == campaign_id).group_by(Campaign.id)

        result = await db.execute(query)
        row = result.first()  # first() вернет (Campaign, amount) или None

        if not row:
            return None

        campaign, amount = row
        campaign.current_amount = amount
        return campaign

    @staticmethod
    async def update(
        db: AsyncSession,
        campaign_id: int,
        schema: CampaignUpdate
    ) -> Optional[Campaign]:
        # Для update нам не обязательно считать сумму, достаточно получить объект
        campaign = await CampaignService.get_by_id_simple(db, campaign_id)
        if not campaign:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(campaign, key, value)

        await db.commit()
        await db.refresh(campaign)

        # Чтобы вернуть красивый ответ с суммой, можно снова вызвать get_by_id
        # или просто вернуть объект (current_amount будет 0 или старым, если не пересчитать)
        return await CampaignService.get_by_id(db, campaign_id)

    # Вспомогательный метод без агрегации (для update/delete)
    @staticmethod
    async def get_by_id_simple(db: AsyncSession, campaign_id: int) -> Optional[Campaign]:
        query = select(Campaign).where(Campaign.id == campaign_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()