import enum
from typing import TYPE_CHECKING, List
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.reviews.models import ClubReview, OrganizationReview
class UserRole(str, enum.Enum):
    MEMBER = "member"           # Обычный пользователь (гость)
    CLUB = "club"               # Клуб
    ORGANIZATION = "organization" # Организатор
    INVESTOR = "investor"       # Инвестор

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        nullable=False,
        index=True
    )

    avatar_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)



    club_reviews: Mapped[List["ClubReview"]] = relationship(
        "ClubReview",
        back_populates="author",
        cascade="all, delete-orphan",
    )
    org_reviews: Mapped[List["OrganizationReview"]] = relationship(
        "OrganizationReview",
        back_populates="author",
        cascade="all, delete-orphan",
    )

    __mapper_args__ = {
        "polymorphic_identity": UserRole.MEMBER,  # По дефолту, если создаем просто User
        "polymorphic_on": role,  # SQLAlchemy смотрит на эту колонку
    }