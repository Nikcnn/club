from sqlalchemy.orm import Session
from apps.organizations.models import Organization
from apps.organizations.schemas import OrganizationCreate
from apps.users.models import UserRole


class OrganizationService:
    @staticmethod
    def create(db: Session, schema: OrganizationCreate) -> Organization:
        # hash = get_password_hash(schema.password)
        hash = "hashed_secret"

        org = Organization(
            email=schema.email,
            hashed_password=hash,
            role=UserRole.ORGANIZATION,

            # Поля Организации
            name=schema.name,
            city=schema.city,
            description=schema.description,
            logo_key=schema.logo_key
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        return org