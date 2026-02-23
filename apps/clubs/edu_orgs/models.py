from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.base import Base
from apps.users.models import User, UserRole


class EducationalOrganizations(Base):
    __tablename__ = "educational_organizations"


    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100), index=True)
    departments: Mapped[List[str]] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    logo_key: Mapped[Optional[str]] = mapped_column(String(512))  # Ссылка на S3
    website: Mapped[Optional[str]] = mapped_column(String(255))
    social_links: Mapped[dict | None] = mapped_column(JSON, default=dict)

    # Настройка полиморфизма SQLAlchemy
    __mapper_args__ = {
        "polymorphic_identity": UserRole.CLUB,
    }
