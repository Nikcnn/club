# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware  # ← ОБЯЗАТЕЛЬНО!
from fastapi.responses import RedirectResponse

from apps.core.settings import settings
from apps.admin.setup import setup_admin
from apps.db.session import sync_engine

# Импорты роутеров
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
from apps.search.routes import router as search_router
from apps.core.routes import router as media_router

from apps.search.qdrant_client import ensure_collection

@asynccontextmanager
async def lifespan(_: FastAPI):
    await ensure_collection()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="API для платформы студенческих клубов ClubVerse",
    lifespan=lifespan,
)

# ==========================================
# MIDDLEWARE (ВАЖНЫЙ ПОРЯДОК!)
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚠️ SessionMiddleware ДОЛЖЕН БЫТЬ ПЕРЕД setup_admin!
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    https_only=False,
    same_site="lax",
)

# Инициализация админки
setup_admin(app, sync_engine)
# ==========================================
# РОУТЕРЫ
# ==========================================
app.include_router(users_router)
app.include_router(clubs_router)
app.include_router(edu_orgs_router)
app.include_router(investors_router)
app.include_router(organizations_router)
app.include_router(funding_router)
app.include_router(payments_router)
app.include_router(competitions_router)
app.include_router(news_router)
app.include_router(reviews_router)
app.include_router(ratings_router)
app.include_router(search_router)
app.include_router(media_router)

# ==========================================
# ROOT
# ==========================================
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}