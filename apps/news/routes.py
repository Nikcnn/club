from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user
from apps.news.schemas import NewsCreate, NewsResponse
from apps.news.services import NewsService
from apps.users.models import UserRole

router = APIRouter(prefix="/news", tags=["News"])

@router.post("/", response_model=NewsResponse)
def create_news(
    schema: NewsCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != UserRole.CLUB:
        raise HTTPException(403, "Only clubs can post news")
    return NewsService.create(db, schema, club_id=current_user.id)