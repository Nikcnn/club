from fastapi import FastAPI
from apps.clubs.router import router as clubs_router
from apps.investors.router import router as investors_router

app = FastAPI()

# Подключаем модульные роутеры
app.include_router(clubs_router)
app.include_router(investors_router)
# app.include_router(auth_router) ...