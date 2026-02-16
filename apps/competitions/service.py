from sqlalchemy.orm import Session
from apps.competitions.models import Competition, CompetitionStatus
from apps.competitions.schemas import CompetitionCreate


class CompetitionService:
    @staticmethod
    def create(db: Session, schema: CompetitionCreate, club_id: int) -> Competition:
        comp = Competition(
            **schema.model_dump(),
            club_id=club_id,
            status=CompetitionStatus.DRAFT
        )
        db.add(comp)
        db.commit()
        db.refresh(comp)
        return comp

    @staticmethod
    def get_list(db: Session, skip: int = 0, limit: int = 10):
        return db.query(Competition).offset(skip).limit(limit).all()