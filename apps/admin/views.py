from sqladmin import ModelView

from apps.clubs.models import Club
from apps.competitions.models import Competition
from apps.funding.models import Campaign, Investment
from apps.investors.models import Investor
from apps.organizations.models import Organization
from apps.payments.models import Payment
from apps.users.models import User


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.role, User.is_active, User.created_at]
    column_searchable_list = [User.email]


class ClubAdmin(ModelView, model=Club):
    column_list = [Club.id, Club.name, Club.category, Club.city, Club.website, Club.created_at]
    column_searchable_list = [Club.name, Club.category, Club.city]


class InvestorAdmin(ModelView, model=Investor):
    column_list = [Investor.id, Investor.email, Investor.company_name, Investor.linkedin_url, Investor.created_at]
    column_searchable_list = [Investor.email, Investor.company_name]


class OrganizationAdmin(ModelView, model=Organization):
    column_list = [Organization.id, Organization.email, Organization.name, Organization.city, Organization.created_at]
    column_searchable_list = [Organization.email, Organization.name, Organization.city]


class CampaignAdmin(ModelView, model=Campaign):
    column_list = [Campaign.id, Campaign.title, Campaign.goal_amount, Campaign.status, Campaign.created_at]
    column_searchable_list = [Campaign.title]


class InvestmentAdmin(ModelView, model=Investment):
    column_list = [Investment.id, Investment.amount, Investment.type, Investment.status, Investment.created_at]


class PaymentAdmin(ModelView, model=Payment):
    column_list = [Payment.id, Payment.amount, Payment.status, Payment.provider, Payment.created_at]


class CompetitionAdmin(ModelView, model=Competition):
    column_list = [Competition.id, Competition.title, Competition.status, Competition.starts_at, Competition.ends_at, Competition.created_at]
    column_searchable_list = [Competition.title]
