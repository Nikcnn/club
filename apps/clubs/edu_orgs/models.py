from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.base import Base
from apps.db.base import TimestampMixin

if TYPE_CHECKING:
    from apps.clubs.models import Club


class EducationalOrganization(Base, TimestampMixin):
    __tablename__ = "educational_organizations"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100), index=True)
    departments: Mapped[List[str] | None] = mapped_column(JSON, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    logo_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    social_links: Mapped[dict | None] = mapped_column(JSON, default=dict)

    clubs: Mapped[List["Club"]] = relationship(
        "Club",
        back_populates="educational_organization",
        lazy="selectin",
    )
