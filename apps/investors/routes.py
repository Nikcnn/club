from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from apps.db.dependencies import get_db
from apps.investors.schemas import InvestorCreate, InvestorResponse
from apps.investors.services import InvestorService

router = APIRouter(prefix="/investors", tags=["Investors"])

@router.post("/register", response_model=InvestorResponse)
def register_investor(schema: InvestorCreate, db: Session = Depends(get_db)):
    return InvestorService.create(db, schema)