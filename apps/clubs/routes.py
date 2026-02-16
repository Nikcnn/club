from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from apps.db.dependencies import get_db
from apps.clubs.schemas import ClubCreate, ClubResponse
from apps.clubs.services import ClubService

router = APIRouter(prefix="/clubs", tags=["Clubs"])

@router.post("/register", response_model=ClubResponse)
async def register_club(      # <--- async def
    schema: ClubCreate,
    db: AsyncSession = Depends(get_db) # Тип сессии AsyncSession
):
    return await ClubService.create(db, schema) # <--- await

@router.get("/{club_id}", response_model=ClubResponse)
async def get_club(club_id: int, db: AsyncSession = Depends(get_db)):
    club = ClubService.get_by_id(db, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club