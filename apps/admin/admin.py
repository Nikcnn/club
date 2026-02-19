from fastapi import FastAPI
from sqladmin import Admin

from apps.admin.views import (
    CampaignAdmin,
    ClubAdmin,
    ClubRatingAdmin,
    ClubReviewAdmin,
    CompetitionAdmin,
    InvestmentAdmin,
    InvestorAdmin,
    NewsAdmin,
    OrganizationAdmin,
    OrganizationRatingAdmin,
    OrganizationReviewAdmin,
    PaymentAdmin,
    PaymentIdempotencyAdmin,
    PaymentStateTransitionLogAdmin,
    UserAdmin,
    WebhookDeliveryLogAdmin,
    WebhookEventAdmin,
)
from apps.db.session import engine


def setup_sqladmin(app: FastAPI) -> Admin:
    """Register SQLAdmin views for all project models."""

    admin = Admin(app=app, engine=engine)

    admin_views = [
        UserAdmin,
        ClubAdmin,
        InvestorAdmin,
        OrganizationAdmin,
        CampaignAdmin,
        InvestmentAdmin,
        PaymentAdmin,
        PaymentIdempotencyAdmin,
        WebhookEventAdmin,
        WebhookDeliveryLogAdmin,
        PaymentStateTransitionLogAdmin,
        CompetitionAdmin,
        NewsAdmin,
        ClubReviewAdmin,
        OrganizationReviewAdmin,
        ClubRatingAdmin,
        OrganizationRatingAdmin,
    ]

    for view in admin_views:
        admin.add_view(view)

    return admin
