from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse

# Импорт настроек
from apps.core.settings import settings

# Импорт роутеров из всех модулей
from apps.users.routes import router as users_router
from apps.clubs.routes import router as clubs_router
from apps.clubs.edu_orgs.routes import router as edu_orgs_router
from apps.investors.routes import router as investors_router
from apps.organizations.routes import router as organizations_router
from apps.funding.routes import router as funding_router
from apps.payments.routes import router as payments_router
from apps.competitions.routes import router as competitions_router
from apps.news.routes import router as news_router
from apps.reviews.routes import router as reviews_router
from apps.ratings.routes import router as ratings_router
from apps.admin.setup import setup_admin
from apps.search.qdrant_client import ensure_collection
from apps.search.routes import router as search_router
from apps.core.routes import router as media_router
@asynccontextmanager
async def lifespan(_: FastAPI):
    await ensure_collection()
    yield


# Создание приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="API для платформы студенческих клубов ClubVerse (Modular Monolith)",
    lifespan=lifespan,
    # Отключаем документацию, если мы в продакшене (опционально)
    # docs_url=None if settings.ENV == "production" else "/docs",
)

# ==========================================
# 1. MIDDLEWARE (CORS)
# ==========================================
# Разрешаем запросы с фронтенда (React/Vue/Mobile)
# В продакшене лучше указать конкретные домены вместо ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация админ-панели (/admin)
setup_admin(app)

# ==========================================
# 2. ПОДКЛЮЧЕНИЕ РОУТЕРОВ (Routes)
# ==========================================

# --- Auth & Users ---
# /users/login, /users/register, /users/me
app.include_router(users_router)

# --- Profiles ---
# /clubs, /investors, /organizations
app.include_router(clubs_router)
app.include_router(edu_orgs_router)
app.include_router(investors_router)
app.include_router(organizations_router)

# --- Features ---
# /funding/campaigns, /funding/investments
app.include_router(funding_router)

# /payments/initiate, /payments/webhook
app.include_router(payments_router)

# /competitions
app.include_router(competitions_router)

# /news
app.include_router(news_router)

# --- Social & Feedback ---
# /reviews
app.include_router(reviews_router)
# /ratings
app.include_router(ratings_router)

# /search
app.include_router(search_router)
# /media
app.include_router(media_router)


# ==========================================
# 3. ROOT ENDPOINT
# ==========================================

@app.get("/", include_in_schema=False)
async def root():
    """
    Редирект с корня на документацию.
    """
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """
    Проверка работоспособности сервиса (Health Check).
    Используется Docker'ом или балансировщиком нагрузки.
    """
    return {"status": "ok", "version": "1.0.0"}
