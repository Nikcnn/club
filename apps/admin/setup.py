from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from apps.core.settings import settings


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
    from apps.ratings.models import ClubRating, OrganizationRating
    from apps.reviews.models import ClubReview, OrganizationReview
    from apps.search.models import SearchEvent, ClickEvent, UserSearchProfile

    class BaseAdmin(ModelView):
        can_export = True
        page_size = 50

    class UserAdmin(BaseAdmin, model=User):
        name = "Пользователь"
        name_plural = "Пользователи"
        can_create = False
        column_list = ["id", "email", "username", "role", "is_active", "created_at"]
        column_searchable_list = ["email", "username"]
        column_sortable_list = ["id", "created_at"]
        form_excluded_columns = ["hashed_password", "club_reviews", "org_reviews", "created_at", "updated_at"]

    admin.add_view(UserAdmin)

    class ClubAdmin(BaseAdmin, model=Club):
        name = "Клуб"
        name_plural = "Клубы"
        can_create = False
        column_list = ["id", "name", "category", "city", "website", "is_active", "created_at"]
        column_searchable_list = ["name", "city"]
        column_sortable_list = ["id", "created_at"]
        form_excluded_columns = [
            "hashed_password",
            "campaigns",
            "news",
            "competitions",
            "reviews",
            "rating",
            "created_at",
            "updated_at",
        ]

    admin.add_view(ClubAdmin)

    class InvestorAdmin(BaseAdmin, model=Investor):
        name = "Инвестор"
        name_plural = "Инвесторы"
        can_create = False
        column_list = ["id", "email", "username", "company_name", "linkedin_url", "is_active", "created_at"]
        column_searchable_list = ["email", "username", "company_name"]
        column_sortable_list = ["id", "created_at"]
        form_excluded_columns = [
            "hashed_password",
            "investments",
            "club_reviews",
            "org_reviews",
            "created_at",
            "updated_at",
        ]

    admin.add_view(InvestorAdmin)

    class OrganizationAdmin(BaseAdmin, model=Organization):
        name = "Организация"
        name_plural = "Организации"
        can_create = False
        column_list = ["id", "name", "email", "city", "website", "is_active", "created_at"]
        column_searchable_list = ["name", "email", "city"]
        column_sortable_list = ["id", "created_at"]
        form_excluded_columns = [
            "hashed_password",
            "reviews",
            "rating",
            "org_reviews",
            "club_reviews",
            "created_at",
            "updated_at",
        ]

    admin.add_view(OrganizationAdmin)

    class CompetitionAdmin(BaseAdmin, model=Competition):
        name = "Соревнование"
        name_plural = "Соревнования"
        column_list = ["id", "club_id", "title", "status", "starts_at", "ends_at", "created_at"]
        column_searchable_list = ["title"]
        column_sortable_list = ["id", "starts_at", "ends_at", "created_at"]
        form_columns = ["club", "title", "description", "starts_at", "ends_at", "photo_key", "status"]

    admin.add_view(CompetitionAdmin)

    class CampaignAdmin(BaseAdmin, model=Campaign):
        name = "Кампания"
        name_plural = "Кампании"
        column_list = ["id", "club_id", "title", "goal_amount", "status", "starts_at", "ends_at", "created_at"]
        column_searchable_list = ["title"]
        column_sortable_list = ["id", "goal_amount", "starts_at", "ends_at", "created_at"]
        form_columns = [
            "club",
            "title",
            "description",
            "goal_amount",
            "starts_at",
            "ends_at",
            "status",
            "cover_key",
            "gallery_keys",
        ]

    admin.add_view(CampaignAdmin)

    class InvestmentAdmin(BaseAdmin, model=Investment):
        name = "Инвестиция"
        name_plural = "Инвестиции"
        column_list = ["id", "campaign_id", "investor_id", "amount", "type", "status", "paid_at", "created_at"]
        column_sortable_list = ["id", "amount", "paid_at", "created_at"]
        form_columns = ["campaign", "investor", "amount", "type", "status", "paid_at"]

    admin.add_view(InvestmentAdmin)

    class NewsAdmin(BaseAdmin, model=News):
        name = "Новость"
        name_plural = "Новости"
        column_list = ["id", "club_id", "title", "is_published", "published_at", "created_at"]
        column_searchable_list = ["title", "body"]
        column_sortable_list = ["id", "published_at", "created_at"]
        form_columns = ["club", "title", "body", "cover_key", "published_at", "is_published"]

    admin.add_view(NewsAdmin)

    class PaymentAdmin(BaseAdmin, model=Payment):
        name = "Платеж"
        name_plural = "Платежи"
        column_list = ["id", "investment_id", "provider", "amount", "status", "confirmed_at", "created_at"]
        column_sortable_list = ["id", "amount", "confirmed_at", "created_at"]
        form_columns = [
            "investment",
            "provider",
            "provider_payment_id",
            "checkout_url",
            "amount",
            "status",
            "idempotency_key",
            "last_event_at",
            "version",
            "confirmed_at",
        ]

    admin.add_view(PaymentAdmin)

    class PaymentIdempotencyAdmin(BaseAdmin, model=PaymentIdempotency):
        name = "Идемпотентность платежа"
        name_plural = "Ключи идемпотентности"
        column_list = ["id", "user_id", "scope", "idempotency_key", "payment_id", "response_code", "created_at"]
        column_searchable_list = ["idempotency_key", "scope"]
        column_sortable_list = ["id", "created_at"]
        form_excluded_columns = ["created_at"]

    admin.add_view(PaymentIdempotencyAdmin)

    class WebhookEventAdmin(BaseAdmin, model=WebhookEvent):
        name = "Webhook событие"
        name_plural = "Webhook события"
        column_list = ["id", "provider", "provider_event_id", "event_type", "signature_valid", "status", "received_at"]
        column_searchable_list = ["provider", "provider_event_id", "event_type"]
        column_sortable_list = ["id", "received_at"]
        form_excluded_columns = ["deliveries", "received_at"]

    admin.add_view(WebhookEventAdmin)

    class ClubRatingAdmin(BaseAdmin, model=ClubRating):
        name = "Рейтинг клуба"
        name_plural = "Рейтинги клубов"
        column_list = ["id", "club_id", "avg_score", "review_count", "updated_at"]
        column_sortable_list = ["id", "avg_score", "review_count", "updated_at"]
        form_columns = ["club", "avg_score", "review_count"]

    admin.add_view(ClubRatingAdmin)

    class OrganizationRatingAdmin(BaseAdmin, model=OrganizationRating):
        name = "Рейтинг организации"
        name_plural = "Рейтинги организаций"
        column_list = ["id", "organization_id", "avg_score", "review_count", "updated_at"]
        column_sortable_list = ["id", "avg_score", "review_count", "updated_at"]
        form_columns = ["organization", "avg_score", "review_count"]

    admin.add_view(OrganizationRatingAdmin)

    class ClubReviewAdmin(BaseAdmin, model=ClubReview):
        name = "Отзыв о клубе"
        name_plural = "Отзывы о клубах"
        column_list = ["id", "club_id", "user_id", "score", "moderation_status", "is_approved", "created_at"]
        column_sortable_list = ["id", "score", "created_at"]
        form_columns = [
            "club",
            "author",
            "text",
            "score",
            "is_approved",
            "moderation_status",
            "toxicity_score",
            "moderation_labels",
        ]

    admin.add_view(ClubReviewAdmin)

    class OrganizationReviewAdmin(BaseAdmin, model=OrganizationReview):
        name = "Отзыв об организации"
        name_plural = "Отзывы об организациях"
        column_list = ["id", "organization_id", "user_id", "score", "moderation_status", "is_approved", "created_at"]
        column_sortable_list = ["id", "score", "created_at"]
        form_columns = [
            "organization",
            "author",
            "text",
            "score",
            "is_approved",
            "moderation_status",
            "toxicity_score",
            "moderation_labels",
        ]

    admin.add_view(OrganizationReviewAdmin)

    class SearchEventAdmin(BaseAdmin, model=SearchEvent):
        name = "Событие поиска"
        name_plural = "События поиска"
        column_list = ["id", "user_id", "query_text", "role", "created_at"]
        column_searchable_list = ["query_text", "role"]
        column_sortable_list = ["id", "created_at"]
        form_excluded_columns = ["created_at"]

    admin.add_view(SearchEventAdmin)

    class ClickEventAdmin(BaseAdmin, model=ClickEvent):
        name = "Событие клика"
        name_plural = "События кликов"
        column_list = ["id", "user_id", "doc_id", "doc_type", "entity_id", "position", "created_at"]
        column_searchable_list = ["doc_id", "doc_type", "entity_id"]
        column_sortable_list = ["id", "position", "created_at"]
        form_excluded_columns = ["created_at"]

    admin.add_view(ClickEventAdmin)

    class UserSearchProfileAdmin(BaseAdmin, model=UserSearchProfile):
        name = "Профиль поиска пользователя"
        name_plural = "Профили поиска пользователей"
        column_list = ["user_id", "top_cities", "top_categories", "top_types", "updated_at"]
        column_sortable_list = ["user_id", "updated_at"]
        form_excluded_columns = ["updated_at"]

    admin.add_view(UserSearchProfileAdmin)
    return admin
