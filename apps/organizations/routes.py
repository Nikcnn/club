from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from apps.db.dependencies import get_db
from apps.organizations.schemas import OrganizationCreate, OrganizationResponse
from apps.organizations.services import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.post("/register", response_model=OrganizationResponse)
def register_organization(schema: OrganizationCreate, db: Session = Depends(get_db)):
    return OrganizationService.create(db, schema)