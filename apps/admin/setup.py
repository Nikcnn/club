from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from apps.core.settings import settings


# ==========================================
# 1. АВТОРИЗАЦИЯ
# ==========================================
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if username == "admin" and password == "admin":
            request.session.update({"admin_token": "secure_token"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "admin_token" in request.session


authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)


# ==========================================
# 2. ИНИЦИАЛИЗАЦИЯ
# ==========================================


# ==========================================
# 3. МОДЕЛИ (закомментировано пока не настроите)
# ==========================================

# 2. ИНИЦИАЛИЗАЦИЯ
# ==========================================
def setup_admin(app: FastAPI, sync_engine):
    admin = Admin(
        app=app,
        engine=sync_engine,
        authentication_backend=authentication_backend,
    )
    from apps.users.models import User
    from apps.clubs.models import Club
    from apps.investors.models import Investor
    from apps.organizations.models import Organization
    from apps.competitions.models import Competition
    from apps.funding.models import Campaign, Investment
    from apps.news.models import News
    from apps.payments.models import Payment, PaymentIdempotency, WebhookEvent
    from apps.ratings.models import RatingBase, ClubRating, OrganizationRating
    from apps.reviews.models import ReviewBase, ClubReview, OrganizationReview
    from apps.search.models import SearchEvent, ClickEvent, UserSearchProfile

    class UserAdmin(ModelView, model=User):
        column_list = "__all__"

    admin.add_view(UserAdmin)

    class ClubAdmin(ModelView, model=Club):
        column_list = "__all__"

    admin.add_view(ClubAdmin)

    class InvestorAdmin(ModelView, model=Investor):
        column_list = "__all__"
    admin.add_view(InvestorAdmin)

    class OrganizationAdmin(ModelView, model=Organization):
        column_list = "__all__"
    admin.add_view(OrganizationAdmin)

    class CompetitionAdmin(ModelView, model=Competition):
        column_list = "__all__"
    admin.add_view(CompetitionAdmin)

    class CampaignAdmin(ModelView, model=Campaign):
        column_list = "__all__"
    admin.add_view(CampaignAdmin)

    class InvestmentAdmin(ModelView, model=Investment):
        column_list = "__all__"
    admin.add_view(InvestmentAdmin)

    class NewsAdmin(ModelView, model=News):
        column_list = "__all__"
    admin.add_view(NewsAdmin)

    class PaymentAdmin(ModelView, model=Payment):
        column_list = "__all__"
    admin.add_view(PaymentAdmin)

    class PaymentIdempotencyAdmin(ModelView, model=PaymentIdempotency):
        column_list = "__all__"
    admin.add_view(PaymentIdempotencyAdmin)

    class WebhookEventAdmin(ModelView, model=WebhookEvent):
        column_list = "__all__"

    admin.add_view(WebhookEventAdmin)

    class ClubRatingAdmin(ModelView, model=ClubRating):
        column_list = "__all__"

    admin.add_view(ClubRatingAdmin)

    class OrganizationRatingAdmin(ModelView, model=OrganizationRating):
        column_list = "__all__"

    admin.add_view(OrganizationRatingAdmin)

    class ClubReviewAdmin(ModelView, model=ClubReview):
        column_list = "__all__"

    admin.add_view(ClubReviewAdmin)

    class OrganizationReviewAdmin(ModelView, model=OrganizationReview):
        column_list = "__all__"

    admin.add_view(OrganizationReviewAdmin)

    class SearchEventAdmin(ModelView, model=SearchEvent):
        column_list = "__all__"

    admin.add_view(SearchEventAdmin)

    class ClickEventAdmin(ModelView, model=ClickEvent):
        column_list = "__all__"

    admin.add_view(ClickEventAdmin)

    class UserSearchProfileAdmin(ModelView, model=UserSearchProfile):
        column_list = "__all__"

    admin.add_view(UserSearchProfileAdmin)
    return admin
