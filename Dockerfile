# Stage 1 — Build
FROM python:3.12-slim AS build

WORKDIR /club-back

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Виртуальное окружение, чтобы копировать одной папкой
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Только зависимости (кэшируется)
COPY requirements.ini .

# ВАЖНО: если torch у тебя как "+cpu", часто нужен pytorch index.
# Если после перехода на 3.12 всё равно не ставится — см. секцию про torch ниже.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.ini

# Stage 2 — Runtime
FROM python:3.12-slim AS runtime

WORKDIR /club-back

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    ENV=production

COPY --from=build /opt/venv /opt/venv

# Код приложения
COPY . .

EXPOSE 8909

# ВАЖНО: тут должно быть "module:app", например "main:app" или "webhook:app"
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "-b", "0.0.0.0:8909", "--timeout", "120"]