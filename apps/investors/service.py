from sqlalchemy.orm import Session
from apps.investors.models import Investor
from apps.investors.schemas import InvestorCreate
from apps.users.models import UserRole


class InvestorService:
    @staticmethod
    def create(db: Session, schema: InvestorCreate) -> Investor:
        # hash = get_password_hash(schema.password)
        hash = "hashed_secret"

        investor = Investor(
            email=schema.email,
            hashed_password=hash,
            role=UserRole.INVESTOR,  # Важно!

            # Поля Инвестора
            bio=schema.bio,
            avatar_key=schema.avatar_key
        )
        db.add(investor)
        db.commit()
        db.refresh(investor)
        return investor