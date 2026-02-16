# apps/db/models.py
from apps.db.base import Base

# Импортируем все модели, чтобы они зарегистрировались в Metadata
from apps.users.models import User
from apps.clubs.models import Club
from apps.investors.models import Investor
from apps.organizations.models import Organization

from apps.campaigns.models import Campaign, Investment, Payment
from apps.competitions.models import Competition
from apps.news.models import News
from apps.reviews.models import ClubReview, OrganizationReview
# from apps.ratings.models import ...