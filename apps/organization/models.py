from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# -------------------------
# Base
# -------------------------
class Base(DeclarativeBase):
    pass


# -------------------------
# Core tables
# -------------------------
class User(Base):
    """
    Было в диаграмме: user(id, name, surname, roles, created_at, contact_url)
    """
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    surname: Mapped[str] = mapped_column(String(255), nullable=False)
    roles: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    contact_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Relations
    captain_clubs: Mapped[List["Club"]] = relationship(
        back_populates="captain",
        foreign_keys="Club.captain_id",
    )
    organizations: Mapped[List["Organization"]] = relationship(back_populates="user")
    investors: Mapped[List["Investor"]] = relationship(back_populates="user")
    news_items: Mapped[List["News"]] = relationship(back_populates="user")
    reviews: Mapped[List["Review"]] = relationship(back_populates="user")
    competition_journal_entries: Mapped[List["CompetitionJournal"]] = relationship(
        back_populates="user"
    )


class EducationOrganization(Base):
    """
    Было в диаграмме: educatacional_organization(id, city, description)
    Исправлено:
      - таблица: education_organization
    """
    __tablename__ = "education_organization"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Relations
    clubs: Mapped[List["Club"]] = relationship(back_populates="education_organization")
    review_links: Mapped[List["ReviewEducationOrganization"]] = relationship(
        back_populates="education_organization"
    )


class Club(Base):
    """
    Было в диаграмме: club(id, category, city, member_count, capitan_id, education_organization_id)
    Исправлено:
      - capitan_id -> captain_id
      - education_organization_id -> edu_org_id (и FK на education_organization)
    """
    __tablename__ = "club"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    captain_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    edu_org_id: Mapped[int] = mapped_column(
        ForeignKey("education_organization.id"),
        nullable=False,
    )

    # Relations
    captain: Mapped["User"] = relationship(
        back_populates="captain_clubs",
        foreign_keys=[captain_id],
    )
    education_organization: Mapped["EducationOrganization"] = relationship(
        back_populates="clubs",
        foreign_keys=[edu_org_id],
    )

    projects: Mapped[List["Project"]] = relationship(back_populates="club")
    trophies: Mapped[List["ClubTrophy"]] = relationship(back_populates="club")

    rating_links: Mapped[List["RatingClub"]] = relationship(back_populates="club")
    review_links: Mapped[List["ReviewClub"]] = relationship(back_populates="club")


class Project(Base):
    """
    Было в диаграмме: projects(id, name, purpose, invest_fund, photo_url, sponsor, club_id)
    """
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    invest_fund: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # В диаграмме sponsor не *_id, значит считаем как текст/название спонсора.
    sponsor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    club_id: Mapped[int] = mapped_column(ForeignKey("club.id"), nullable=False)

    # Relations
    club: Mapped["Club"] = relationship(back_populates="projects")


class Organization(Base):
    """
    Было в диаграмме: organization(id, name, law_role, user_id)
    """
    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    law_role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    # Relations
    user: Mapped["User"] = relationship(back_populates="organizations")

    rating_links: Mapped[List["RatingOrganization"]] = relationship(
        back_populates="organization"
    )
    review_links: Mapped[List["ReviewOrganization"]] = relationship(
        back_populates="organization"
    )


class Investor(Base):
    """
    Было в диаграмме: investor(id, user_id, law_role, investing_fund_count)
    """
    __tablename__ = "investor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    law_role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    investing_fund_count: Mapped[Optional[float]] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    # Relations
    user: Mapped["User"] = relationship(back_populates="investors")
    rating_links: Mapped[List["RatingInvestor"]] = relationship(back_populates="investor")


class News(Base):
    """
    Было в диаграмме: news(id, caption, photo_link, user_id, created_at)
    """
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    caption: Mapped[str] = mapped_column(String(2000), nullable=False)
    photo_link: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relations
    user: Mapped["User"] = relationship(back_populates="news_items")


# -------------------------
# Competitions + trophies + journal
# -------------------------
class Competition(Base):
    """
    Было в диаграмме: competion(..., descr, descr_pdf_link)
    Исправлено:
      - таблица: competition
      - descr -> description
      - descr_pdf_link -> description_pdf_link
    """
    __tablename__ = "competition"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    start_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    prize_fund: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)

    city: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    description: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)
    description_pdf_link: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Relations
    trophies: Mapped[List["ClubTrophy"]] = relationship(back_populates="competition")
    journal_entries: Mapped[List["CompetitionJournal"]] = relationship(
        back_populates="competition"
    )


class ClubTrophy(Base):
    """
    Было в диаграмме: club_trophys(id, club_id, competion_id)
    Исправлено:
      - таблица: club_trophies
      - competion_id -> competition_id
    """
    __tablename__ = "club_trophies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("club.id"), nullable=False)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competition.id"), nullable=False)

    # Relations
    club: Mapped["Club"] = relationship(back_populates="trophies")
    competition: Mapped["Competition"] = relationship(back_populates="trophies")


class CompetitionJournal(Base):
    """
    Было в диаграмме: competions_journal(id, id_competion, id_user, is_visit)
    Исправлено:
      - таблица: competitions_journal
      - id_competion -> competition_id
      - id_user -> user_id
    """
    __tablename__ = "competitions_journal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competition.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    is_visit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relations
    competition: Mapped["Competition"] = relationship(back_populates="journal_entries")
    user: Mapped["User"] = relationship(back_populates="competition_journal_entries")


# -------------------------
# Rating + link tables
# -------------------------
class Rating(Base):
    """
    Было в диаграмме: raiting(id, raiting_value, coeficent_value)
    Исправлено:
      - таблица: rating
      - raiting_value -> rating_value
      - coeficent_value -> coefficient_value
    """
    __tablename__ = "rating"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rating_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    coefficient_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relations
    club_links: Mapped[List["RatingClub"]] = relationship(back_populates="rating")
    org_links: Mapped[List["RatingOrganization"]] = relationship(back_populates="rating")
    investor_links: Mapped[List["RatingInvestor"]] = relationship(back_populates="rating")


class RatingClub(Base):
    """
    Было в диаграмме: raiting_club(id, club_id, ratinig_id)
    Исправлено:
      - таблица: rating_club
      - ratinig_id -> rating_id
    """
    __tablename__ = "rating_club"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("club.id"), nullable=False)
    rating_id: Mapped[int] = mapped_column(ForeignKey("rating.id"), nullable=False)

    club: Mapped["Club"] = relationship(back_populates="rating_links")
    rating: Mapped["Rating"] = relationship(back_populates="club_links")


class RatingOrganization(Base):
    """
    Было в диаграмме: raiting_organization(id, organization_id, ratinig_id)
    Исправлено:
      - таблица: rating_organization
      - ratinig_id -> rating_id
    """
    __tablename__ = "rating_organization"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id"), nullable=False)
    rating_id: Mapped[int] = mapped_column(ForeignKey("rating.id"), nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="rating_links")
    rating: Mapped["Rating"] = relationship(back_populates="org_links")


class RatingInvestor(Base):
    """
    Было в диаграмме: raiting_investor(id, investor_id, ratinig_id)
    Исправлено:
      - таблица: rating_investor
      - ratinig_id -> rating_id
    """
    __tablename__ = "rating_investor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investor_id: Mapped[int] = mapped_column(ForeignKey("investor.id"), nullable=False)
    rating_id: Mapped[int] = mapped_column(ForeignKey("rating.id"), nullable=False)

    investor: Mapped["Investor"] = relationship(back_populates="rating_links")
    rating: Mapped["Rating"] = relationship(back_populates="investor_links")


# -------------------------
# Reviews + link tables
# -------------------------
class Review(Base):
    """
    Было в диаграмме: review(id, caption, user_id, rate, created_at)
    """
    __tablename__ = "review"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    caption: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relations
    user: Mapped["User"] = relationship(back_populates="reviews")

    club_links: Mapped[List["ReviewClub"]] = relationship(back_populates="review")
    org_links: Mapped[List["ReviewOrganization"]] = relationship(back_populates="review")
    edu_org_links: Mapped[List["ReviewEducationOrganization"]] = relationship(
        back_populates="review"
    )


class ReviewClub(Base):
    """
    Было в диаграмме: review_club(id, review_id, club_id)
    """
    __tablename__ = "review_club"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("review.id"), nullable=False)
    club_id: Mapped[int] = mapped_column(ForeignKey("club.id"), nullable=False)

    review: Mapped["Review"] = relationship(back_populates="club_links")
    club: Mapped["Club"] = relationship(back_populates="review_links")


class ReviewOrganization(Base):
    """
    Было в диаграмме: review_organizational(id, organization_id, review_id)
    Исправлено:
      - таблица: review_organization
    """
    __tablename__ = "review_organization"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id"), nullable=False)
    review_id: Mapped[int] = mapped_column(ForeignKey("review.id"), nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="review_links")
    review: Mapped["Review"] = relationship(back_populates="org_links")


class ReviewEducationOrganization(Base):
    """
    Было в диаграмме: review_edu_org(id, edu_org_id, review_id)
    Важно: edu_org_id ссылается на education_organization
    """
    __tablename__ = "review_edu_org"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edu_org_id: Mapped[int] = mapped_column(
        ForeignKey("education_organization.id"),
        nullable=False,
    )
    review_id: Mapped[int] = mapped_column(ForeignKey("review.id"), nullable=False)

    education_organization: Mapped["EducationOrganization"] = relationship(
        back_populates="review_links",
        foreign_keys=[edu_org_id],
    )
    review: Mapped["Review"] = relationship(back_populates="edu_org_links")
