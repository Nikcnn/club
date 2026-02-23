from fastapi import FastAPI
from fastapi_amis_admin.admin import admin
from fastapi_amis_admin.admin.settings import Settings
from fastapi_amis_admin.admin.site import AdminSite

from apps.core.settings import settings
from apps.users.models import User
from apps.clubs.models import Club
from apps.investors.models import Investor
from apps.organizations.models import Organization


site = AdminSite(
    settings=Settings(
        database_url_async=settings.DATABASE_URL,
        site_title="ClubVerse Admin",
        site_header="ClubVerse Admin",
    )
)


@site.register_admin
class UserAdmin(admin.ModelAdmin):
    page_schema = "Пользователи"
    model = User


@site.register_admin
class ClubAdmin(admin.ModelAdmin):
    page_schema = "Клубы"
    model = Club


@site.register_admin
class InvestorAdmin(admin.ModelAdmin):
    page_schema = "Инвесторы"
    model = Investor


@site.register_admin
class OrganizationAdmin(admin.ModelAdmin):
    page_schema = "Организации"
    model = Organization


def setup_admin(app: FastAPI) -> None:
    """Подключает fastapi-amis-admin к основному приложению."""
    site.mount_app(app)
