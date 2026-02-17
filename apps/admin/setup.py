from sqladmin import Admin

from apps.admin.auth import AdminAuthBackend
from apps.admin.views import (
    CampaignAdmin,
    ClubAdmin,
    CompetitionAdmin,
    InvestmentAdmin,
    InvestorAdmin,
    OrganizationAdmin,
    PaymentAdmin,
    UserAdmin,
)
from apps.core.settings import settings
from apps.db.session import engine


def setup_admin(app):
    auth_backend = AdminAuthBackend(secret_key=settings.SECRET_KEY)
    admin = Admin(app=app, engine=engine, authentication_backend=auth_backend)

    admin.add_view(UserAdmin)
    admin.add_view(ClubAdmin)
    admin.add_view(InvestorAdmin)
    admin.add_view(OrganizationAdmin)
    admin.add_view(CampaignAdmin)
    admin.add_view(InvestmentAdmin)
    admin.add_view(PaymentAdmin)
    admin.add_view(CompetitionAdmin)

    return admin
