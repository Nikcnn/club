Ниже — подробная карта эндпоинтов в этом FastAPI-проекте.
Что я просмотрел

Использовал команды:

    rg --files

    rg "@router\.(get|post|put|patch|delete)" apps/*/routes.py apps/*/*/routes.py

    nl -ba main.py | sed -n '1,260p'

    nl -ba apps/*/routes.py ... (по каждому модулю отдельно, чтобы поднять префиксы, методы, параметры и проверки ролей)

Общая структура API

Все роутеры подключаются в main.py: users, clubs, educational organizations, investors, organizations, funding, payments, competitions, news, reviews, ratings, search, media. Там же есть:

    GET / → редирект на /docs

    GET /health → {status: "ok", version: "1.0.0"}.

1) Users & Auth (/users)

Префикс: /users.

    POST /users/register
    Регистрация обычного пользователя, проверка уникальности email.

    POST /users/login
    Логин через OAuth2PasswordRequestForm, возвращает access_token + refresh_token.

    POST /users/refresh
    Принимает refresh_token в JSON, валидирует JWT тип refresh, выдает новый access-token.

    GET /users/me
    Профиль текущего авторизованного пользователя (get_current_user).

    POST /users/me/avatar
    Загрузка аватара (multipart file), запись ключа в MinIO/S3.
    Все это видно в декораторах и теле функций (включая Depends(get_current_user)).

2) Clubs (/clubs)

Префикс: /clubs.

    POST /clubs/register — регистрация клуба.

    GET /clubs/ — каталог клубов, фильтры: city, category, search, пагинация skip/limit.

    GET /clubs/{club_id} — профиль клуба.

    PATCH /clubs/me — обновление своего профиля (только роль CLUB).

    POST /clubs/me/logo — загрузка логотипа клуба (только роль CLUB).

3) Educational Organizations (/educational-organizations)

Префикс: /educational-organizations.
⚠️ В текущей реализации доступ фактически только для current_user.role == 'admin'.

    POST /educational-organizations/

    GET /educational-organizations/ (фильтр city)

    GET /educational-organizations/{edu_org_id}

    PATCH /educational-organizations/{edu_org_id}

    DELETE /educational-organizations/{edu_org_id}

    POST /educational-organizations/{edu_org_id}/logo (upload logo)
    Во всех методах есть admin-check + 404 при отсутствии сущности (где применимо).

4) Investors (/investors)

Префикс: /investors.

    POST /investors/register — регистрация инвестора + проверка уникального email.

    GET /investors/ — список (skip/limit).

    GET /investors/{investor_id} — профиль по id.

    PATCH /investors/me — редактирование своего профиля (только INVESTOR).

    POST /investors/me/avatar — загрузка своего аватара (только INVESTOR).

5) Organizations (/organizations)

Префикс: /organizations.

    POST /organizations/register — регистрация организации, проверка email.

    GET /organizations/ — каталог, фильтры city, search, плюс skip/limit.

    GET /organizations/{org_id} — профиль организации.

    PATCH /organizations/me — обновление профиля (только ORGANIZATION).

    POST /organizations/me/logo — загрузка лого (только ORGANIZATION).

6) Funding (/funding)

Префикс: /funding.
Campaigns

    GET /funding/campaigns/ — список кампаний, club_id, skip, limit.

    POST /funding/campaigns/ — создать кампанию (только CLUB).

    POST /funding/campaigns/{campaign_id}/cover — загрузка обложки (владелец кампании).

    POST /funding/campaigns/{campaign_id}/gallery — добавить фото в галерею (владелец).

    GET /funding/campaigns/{campaign_id}/ — детали кампании.

    PATCH /funding/campaigns/{campaign_id}/ — обновить (только владелец).

Investments

    POST /funding/investments/ — создать инвестицию (проверка существования кампании).

    GET /funding/investments/my/ — мои инвестиции.

    GET /funding/investments/{investment_id}/ — детали инвестиции (только владелец).

7) Payments (/payments)

Префикс: /payments.

    POST /payments/initiate — инициировать платеж (auth required).

    GET /payments/{payment_id} — статус платежа (auth required).

    POST /payments/webhook/simulate — симуляция webhook (для тестовой обработки статусов).
    Есть маппинг доменных ошибок в HTTP-коды (400/404/409).

8) Competitions (/competitions)

Префикс: /competitions.

    POST /competitions/ — создать соревнование (только CLUB).

    GET /competitions/ — список, фильтры status, club_id, плюс skip/limit.

    GET /competitions/{comp_id} — детали.

    PATCH /competitions/{comp_id} — обновление (владелец).

    POST /competitions/{comp_id}/photo — фото соревнования (владелец).

    POST /competitions/{comp_id}/subscribe — подписаться на соревнование.

    DELETE /competitions/{comp_id}/subscribe — отписаться.

9) News (/news)

Префикс: /news.

    GET /news/ — лента новостей, фильтр club_id, skip/limit.

    GET /news/{news_id} — новость по id.

    POST /news/ — создать новость (только CLUB).

    PATCH /news/{news_id} — редактировать (только автор).

    DELETE /news/{news_id} — удалить (только автор).

    POST /news/{news_id}/cover — загрузить обложку (только автор).

10) Reviews (/reviews)

Префикс: /reviews.

    POST /reviews/club/{club_id} — оставить отзыв клубу (auth).

    POST /reviews/organization/{org_id} — оставить отзыв организации (auth).

    GET /reviews/club/{club_id} — список отзывов клуба.

    GET /reviews/organization/{org_id} — список отзывов организации.

11) Ratings (/ratings)

Префикс: /ratings.

    GET /ratings/club/{club_id} — рейтинг клуба.

    GET /ratings/organization/{org_id} — рейтинг организации.

12) Search (/search)

Префикс: /search.

    GET /search/health — health поиска + статус Qdrant и телеметрии.

    POST /search/reindex — переиндексация (allow_all, т.е. без реального ограничения по auth в этом роуте).

    POST /search/click — лог клика по результату (требует авторизацию).

    GET /search/recommend — персонализированные рекомендации (требует авторизацию), параметры top_k, type.

    GET /search — семантический поиск, параметры:
    q (min 2), top_k, type, city, category, status, role_boost, track;
    может работать анонимно, но персонализация/трекинг зависят от наличия авторизации и флагов.
    Логика optional/required user и параметры подробно заданы прямо в файле роутов.

13) Media (/media)

Префикс: /media.

    GET /media/public-url?object_key=... — вернуть публичный URL объекта в MinIO/S3 по ключу
