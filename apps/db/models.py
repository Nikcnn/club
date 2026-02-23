# apps/db/models.py
from apps.db.base import Base

# 1. Users & Profiles
from apps.users.models import User
from apps.clubs.models import Club
from apps.investors.models import Investor
from apps.organizations.models import Organization

# 2. Funding (Campaigns, Investments, Payments)
# Мы объединили всё это в папке apps/funding
from apps.funding.models import Campaign, Investment
from apps.payments.models import Payment

# 3. Features
from apps.competitions.models import Competition
from apps.news.models import News
from apps.reviews.models import ClubReview, OrganizationReview
from apps.ratings.models import ClubRating, OrganizationRating

# 4. Search tracking
from apps.search.models import SearchEvent, ClickEvent, UserSearchProfile

from apps.clubs.edu_orgs.models import EducationalOrganization