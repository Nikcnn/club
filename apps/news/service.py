from sqlalchemy.orm import Session
from apps.news.models import News
from apps.news.schemas import NewsCreate

class NewsService:
    @staticmethod
    def create(db: Session, schema: NewsCreate, club_id: int) -> News:
        news = News(
            **schema.model_dump(),
            club_id=club_id
        )
        db.add(news)
        db.commit()
        db.refresh(news)
        return news