from sqladmin import ModelView

from apps.clubs.models import Club
from apps.competitions.models import Competition
from apps.funding.models import Campaign, Investment
from apps.investors.models import Investor
from apps.news.models import News
from apps.organizations.models import Organization
from apps.payments.models import (
    Payment,
    PaymentIdempotency,
    PaymentStateTransitionLog,
    WebhookDeliveryLog,
    WebhookEvent,
)
from apps.ratings.models import ClubRating, OrganizationRating
from apps.reviews.models import ClubReview, OrganizationReview
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


class PaymentIdempotencyAdmin(ModelView, model=PaymentIdempotency):
    column_list = [
        PaymentIdempotency.id,
        PaymentIdempotency.user_id,
        PaymentIdempotency.scope,
        PaymentIdempotency.idempotency_key,
        PaymentIdempotency.response_code,
        PaymentIdempotency.created_at,
    ]


class WebhookEventAdmin(ModelView, model=WebhookEvent):
    column_list = [
        WebhookEvent.id,
        WebhookEvent.provider,
        WebhookEvent.event_type,
        WebhookEvent.status,
        WebhookEvent.received_at,
    ]


class WebhookDeliveryLogAdmin(ModelView, model=WebhookDeliveryLog):
    column_list = [
        WebhookDeliveryLog.id,
        WebhookDeliveryLog.webhook_event_id,
        WebhookDeliveryLog.attempt_no,
        WebhookDeliveryLog.processed,
        WebhookDeliveryLog.http_status,
        WebhookDeliveryLog.created_at,
    ]


class PaymentStateTransitionLogAdmin(ModelView, model=PaymentStateTransitionLog):
    column_list = [
        PaymentStateTransitionLog.id,
        PaymentStateTransitionLog.payment_id,
        PaymentStateTransitionLog.from_status,
        PaymentStateTransitionLog.to_status,
        PaymentStateTransitionLog.actor_type,
        PaymentStateTransitionLog.created_at,
    ]


class CompetitionAdmin(ModelView, model=Competition):
    column_list = [Competition.id, Competition.title, Competition.status, Competition.starts_at, Competition.ends_at, Competition.created_at]
    column_searchable_list = [Competition.title]


class NewsAdmin(ModelView, model=News):
    column_list = [News.id, News.club_id, News.title, News.is_published, News.published_at, News.created_at]
    column_searchable_list = [News.title]


class ClubReviewAdmin(ModelView, model=ClubReview):
    column_list = [ClubReview.id, ClubReview.club_id, ClubReview.user_id, ClubReview.score, ClubReview.is_approved, ClubReview.created_at]


class OrganizationReviewAdmin(ModelView, model=OrganizationReview):
    column_list = [
        OrganizationReview.id,
        OrganizationReview.organization_id,
        OrganizationReview.user_id,
        OrganizationReview.score,
        OrganizationReview.is_approved,
        OrganizationReview.created_at,
    ]


class ClubRatingAdmin(ModelView, model=ClubRating):
    column_list = [ClubRating.id, ClubRating.club_id, ClubRating.avg_score, ClubRating.review_count, ClubRating.created_at]


class OrganizationRatingAdmin(ModelView, model=OrganizationRating):
    column_list = [
        OrganizationRating.id,
        OrganizationRating.organization_id,
        OrganizationRating.avg_score,
        OrganizationRating.review_count,
        OrganizationRating.created_at,
    ]
