from sqlalchemy.orm import Session
from apps.reviews.models import ClubReview, OrganizationReview
from apps.reviews.schemas import ReviewCreate


class ReviewService:
    @staticmethod
    def add_club_review(db: Session, schema: ReviewCreate, user_id: int, club_id: int):
        # Проверка: не оставлял ли уже отзыв
        # existing = db.query(ClubReview).filter_by(user_id=user_id, club_id=club_id).first()
        # if existing: raise ...

        review = ClubReview(
            user_id=user_id,
            club_id=club_id,
            text=schema.text,
            score=schema.score
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def add_org_review(db: Session, schema: ReviewCreate, user_id: int, org_id: int):
        review = OrganizationReview(
            user_id=user_id,
            organization_id=org_id,
            text=schema.text,
            score=schema.score
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review