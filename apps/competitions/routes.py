from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user
from apps.competitions.schemas import CompetitionCreate, CompetitionResponse
from apps.competitions.services import CompetitionService
from apps.users.models import User, UserRole

router = APIRouter(prefix="/competitions", tags=["Competitions"])

@router.post("/", response_model=CompetitionResponse)
def create_competition(
    schema: CompetitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.CLUB:
        raise HTTPException(403, "Only clubs can create competitions")
    return CompetitionService.create(db, schema, club_id=current_user.id)

@router.get("/", response_model=list[CompetitionResponse])
def list_competitions(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return CompetitionService.get_list(db, skip, limit)