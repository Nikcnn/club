from sqlalchemy.orm import Session
from apps.campaigns.models import Campaign, Investment, CampaignStatus
from apps.campaigns.schemas import CampaignCreate, InvestmentCreate

class CampaignService:
    @staticmethod
    def create_campaign(db: Session, schema: CampaignCreate, club_id: int) -> Campaign:
        campaign = Campaign(
            **schema.model_dump(),
            club_id=club_id,
            status=CampaignStatus.ACTIVE # Или DRAFT
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def create_investment(db: Session, schema: InvestmentCreate, campaign_id: int, user_id: int):
        # Тут можно добавить проверку статуса кампании
        investment = Investment(
            campaign_id=campaign_id,
            user_id=user_id,
            amount=schema.amount,
            currency=schema.currency,
            status="pending"
        )
        db.add(investment)
        db.commit()
        db.refresh(investment)
        return investment