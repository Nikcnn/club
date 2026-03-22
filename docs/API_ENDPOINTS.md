# Полная документация по API endpoints

> Базовый URL: `http://<host>:<port>`
>
> Авторизация для защищённых ручек: заголовок `Authorization: Bearer <access_token>`.
>
> Формат ответов с ошибками валидации FastAPI: `422 Unprocessable Entity`.

## Общие служебные endpoints

### `GET /health`
- **Назначение:** проверка доступности сервиса.
- **Тело запроса:** нет.
- **Ответ `200`:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## Users & Auth (`/users`)

### `POST /users/register`
- **Доступ:** публичный.
- **Тело (JSON):**
  - `email` (email, обязательно)
  - `password` (string, обязательно)
  - `avatar_key` (string | null, опционально)
- **Ответ `201` (`UserResponseBase`):**
  - `id`, `email`, `username`, `avatar_key`, `role`, `is_active`, `created_at`
- **Ошибки:**
  - `400` — пользователь с таким email уже существует.

### `POST /users/login`
- **Доступ:** публичный.
- **Тело:** `application/x-www-form-urlencoded` (OAuth2PasswordRequestForm)
  - `username` (используется как email)
  - `password`
- **Ответ `200` (`Token`):**
  - `access_token`, `refresh_token`, `token_type` (`bearer`)
- **Ошибки:**
  - `401` — неверные email/пароль.

### `POST /users/refresh`
- **Доступ:** публичный.
- **Тело (JSON):**
  - `refresh_token` (string, обязательно)
- **Ответ `200` (`Token`):**
  - новый `access_token`, тот же `refresh_token`, `token_type`
- **Ошибки:**
  - `401` — токен невалидный/не refresh/пользователь неактивен.

### `GET /users/me`
- **Доступ:** только авторизованный пользователь.
- **Тело:** нет.
- **Ответ `200` (`UserResponseBase`).**

### `POST /users/me/avatar`
- **Доступ:** только авторизованный пользователь.
- **Тело:** `multipart/form-data`
  - `avatar` (файл, обязательно)
- **Ответ `200` (`UserResponseBase`)** с обновлённым `avatar_key`.

---

## Clubs (`/clubs`)

### `POST /clubs/register`
- **Доступ:** публичный.
- **Тело (JSON, `ClubCreate`):**
  - `name` (2..100)
  - `category` (string)
  - `city` (string)
  - `description` (string | null)
  - `website` (string | null)
  - `social_links` (object `{key: value}` | null)
  - `email` (email)
  - `password` (string, min 6)
- **Ответ `201` (`ClubResponse`):**
  - поля клуба + `id`, `email`, `logo_key`.

### `GET /clubs/`
- **Доступ:** публичный.
- **Query params:**
  - `city` (опционально)
  - `category` (опционально)
  - `search` (опционально)
  - `skip` (int, default 0)
  - `limit` (int, default 20)
- **Ответ `200`:** массив `ClubResponse`.

### `GET /clubs/{club_id}`
- **Доступ:** публичный.
- **Path params:** `club_id` (int)
- **Ответ `200` (`ClubResponse`).**
- **Ошибки:** `404` — клуб не найден.

### `PATCH /clubs/me`
- **Доступ:** только роль `club`.
- **Тело (JSON, `ClubUpdate`):** любые из полей
  `name`, `category`, `city`, `description`, `website`, `social_links`, `logo_key`.
- **Ответ `200` (`ClubResponse`).**
- **Ошибки:**
  - `403` — если текущий пользователь не клуб.

---

## Investors (`/investors`)

### `POST /investors/register`
- **Доступ:** публичный.
- **Тело (JSON, `InvestorCreate`):**
  - `bio`, `company_name`, `linkedin_url`, `avatar_key` (все опциональны)
  - `email` (email, обязательно)
  - `password` (min 6, обязательно)
- **Ответ `201` (`InvestorResponse`):**
  - `id`, `email`, `role`, `is_active`, профильные поля.
- **Ошибки:** `400` — email уже зарегистрирован.

### `GET /investors/`
- **Доступ:** публичный.
- **Query params:** `skip` (default 0), `limit` (default 20)
- **Ответ `200`:** массив `InvestorResponse`.

### `GET /investors/{investor_id}`
- **Доступ:** публичный.
- **Ответ `200` (`InvestorResponse`).**
- **Ошибки:** `404` — инвестор не найден.

### `PATCH /investors/me`
- **Доступ:** только роль `investor`.
- **Тело (JSON, `InvestorUpdate`):**
  - `bio`, `company_name`, `linkedin_url`, `avatar_key` (все опциональны)
- **Ответ `200` (`InvestorResponse`).**
- **Ошибки:** `403` — если пользователь не инвестор.

---

## Organizations (`/organizations`)

### `POST /organizations/register`
- **Доступ:** публичный.
- **Тело (JSON, `OrganizationCreate`):**
  - `name` (2..200), `city` (обяз.)
  - `description`, `website`, `logo_key` (опционально)
  - `email` (email), `password` (min 6)
- **Ответ `201` (`OrganizationResponse`).**
- **Ошибки:** `400` — email уже зарегистрирован.

### `GET /organizations/`
- **Доступ:** публичный.
- **Query params:**
  - `city` (опционально)
  - `search` (опционально)
  - `skip` (default 0)
  - `limit` (default 20)
- **Ответ `200`:** массив `OrganizationResponse`.

### `GET /organizations/{org_id}`
- **Доступ:** публичный.
- **Ответ `200` (`OrganizationResponse`).**
- **Ошибки:** `404` — организация не найдена.

### `PATCH /organizations/me`
- **Доступ:** только роль `organization`.
- **Тело (JSON, `OrganizationUpdate`):**
  - `name`, `city`, `description`, `website`, `logo_key` (опционально)
- **Ответ `200` (`OrganizationResponse`).**
- **Ошибки:** `403` — если пользователь не организация.

---

## Funding (`/funding`)

### Campaigns

### `GET /funding/campaigns/`
- **Доступ:** публичный.
- **Query params:**
  - `club_id` (int, опционально)
  - `skip` (default 0)
  - `limit` (default 100)
- **Ответ `200`:** массив `CampaignResponse`.

### `POST /funding/campaigns/`
- **Доступ:** только роль `club`.
- **Тело (JSON, `CampaignCreate`):**
  - `title` (<= 200)
  - `description`
  - `goal_amount` (Decimal > 0)
  - `starts_at` (datetime)
  - `ends_at` (datetime, строго позже `starts_at`)
  - `cover_key` (string | null)
  - `gallery_keys` (array[string], default `[]`)
- **Ответ `201` (`CampaignResponse`):**
  - все поля кампании + `id`, `club_id`, `status`, `created_at`, `updated_at`, `current_amount`
- **Ошибки:** `403` — если не клуб.

### `GET /funding/campaigns/{campaign_id}/`
- **Доступ:** публичный.
- **Ответ `200` (`CampaignResponse`).**
- **Ошибки:** `404` — кампания не найдена.

### `PATCH /funding/campaigns/{campaign_id}/`
- **Доступ:** авторизованный владелец кампании.
- **Тело (JSON, `CampaignUpdate`):** любые поля из
  `title`, `description`, `goal_amount`, `starts_at`, `ends_at`, `status`, `cover_key`, `gallery_keys`.
- **Ответ `200` (`CampaignResponse`).**
- **Ошибки:**
  - `404` — кампания не найдена.
  - `403` — если пользователь не владелец кампании.

### Investments

### `POST /funding/investments/`
- **Доступ:** авторизованный пользователь.
- **Тело (JSON, `InvestmentCreate`):**
  - `campaign_id` (int, обязательно)
  - `amount` (Decimal > 0)
  - `type` (enum, default `donation`): `donation | investment | sponsorship`
- **Ответ `201` (`InvestmentResponse`).**
- **Ошибки:** `404` — целевая кампания не найдена.

### `GET /funding/investments/my/`
- **Доступ:** авторизованный пользователь.
- **Ответ `200`:** массив `InvestmentResponse` для текущего пользователя.

### `GET /funding/investments/{investment_id}/`
- **Доступ:** только владелец инвестиции.
- **Ответ `200` (`InvestmentResponse`).**
- **Ошибки:**
  - `404` — инвестиция не найдена.
  - `403` — чужая инвестиция.

---

## Payments (`/payments`)

### `POST /payments/initiate`
- **Доступ:** авторизованный пользователь.
- **Тело (JSON, `PaymentInitiate`):**
  - `investment_id` (int, обязательно)
  - `provider` (enum, default `paybox`): `paybox | stripe`
  - `idempotency_key` (string | null, max 128)
- **Ответ `201` (`PaymentResponse`):**
  - `id`, `investment_id`, `amount`, `status`, `provider`, `checkout_url`, `idempotency_key`, `created_at`, `confirmed_at`
- **Ошибки:** `400` — бизнес-валидация оплаты.

### `GET /payments/{payment_id}`
- **Доступ:** авторизованный пользователь.
- **Ответ `200` (`PaymentResponse`).**
- **Ошибки:** `404` — платёж не найден.

### `POST /payments/webhook/simulate`
- **Доступ:** публичный (техническая ручка симуляции webhook).
- **Тело (JSON, `PaymentWebhookData`):**
  - `provider_payment_id` (string)
  - `provider_event_id` (string | null)
  - `event_type` (string, default `payment_status`)
  - `status` (string)
  - `signature` (string | null)
  - `payload` (object, default `{}`)
- **Ответ `200` (`PaymentResponse`)** с новым состоянием платежа.
- **Ошибки:**
  - `409` — конфликт недопустимого перехода состояния.
  - `404` — платёж/сущность не найдена.

---

## Competitions (`/competitions`)

### `POST /competitions/`
- **Доступ:** только роль `club`.
- **Тело (JSON, `CompetitionCreate`):**
  - `title` (<= 200)
  - `description` (опционально)
  - `starts_at` (datetime)
  - `ends_at` (datetime, позже `starts_at`)
- **Ответ `201` (`CompetitionResponse`).**
- **Ошибки:** `403` — если не клуб.

### `GET /competitions/`
- **Доступ:** публичный.
- **Query params:**
  - `status` (`draft | active | finished | canceled`, опционально)
  - `club_id` (int, опционально)
  - `skip` (default 0), `limit` (default 20)
- **Ответ `200`:** массив `CompetitionResponse`.

### `GET /competitions/{comp_id}`
- **Доступ:** публичный.
- **Ответ `200` (`CompetitionResponse`).**
- **Ошибки:** `404` — соревнование не найдено.

### `PATCH /competitions/{comp_id}`
- **Доступ:** только владелец соревнования (клуб).
- **Тело (JSON, `CompetitionUpdate`):**
  - `title`, `description`, `starts_at`, `ends_at`, `status` (все опционально)
- **Ответ `200` (`CompetitionResponse`).**
- **Ошибки:** `404`, `403`.

### `POST /competitions/{comp_id}/photo`
- **Доступ:** только владелец соревнования (клуб).
- **Тело:** `multipart/form-data`
  - `photo` (файл, обязательно)
- **Ответ `200` (`CompetitionResponse`)** с обновлённым `photo_key`.
- **Ошибки:** `404`, `403`.

---

## News (`/news`)

### `GET /news/`
- **Доступ:** публичный.
- **Query params:**
  - `club_id` (опционально)
  - `skip` (default 0)
  - `limit` (default 20)
- **Ответ `200`:** массив `NewsResponse`.

### `GET /news/{news_id}`
- **Доступ:** публичный.
- **Ответ `200` (`NewsResponse`).**
- **Ошибки:** `404` — новость не найдена.

### `POST /news/`
- **Доступ:** только роль `club`.
- **Тело (JSON, `NewsCreate`):**
  - `title` (<= 200)
  - `body`
  - `cover_key` (string | null)
  - `is_published` (bool, default `true`)
- **Ответ `201` (`NewsResponse`).**
- **Ошибки:** `403` — если не клуб.

### `PATCH /news/{news_id}`
- **Доступ:** только автор новости (клуб).
- **Тело (JSON, `NewsUpdate`):**
  - `title`, `body`, `cover_key`, `is_published` (все опционально)
- **Ответ `200` (`NewsResponse`).**
- **Ошибки:** `404`, `403`.

### `DELETE /news/{news_id}`
- **Доступ:** только автор новости (клуб).
- **Тело:** нет.
- **Ответ `204 No Content`.
- **Ошибки:** `404`, `403`.

---

## Reviews (`/reviews`)

### `POST /reviews/club/{club_id}`
- **Доступ:** авторизованный пользователь.
- **Тело (JSON, `ReviewCreate`):**
  - `text` (string)
  - `score` (int от 1 до 5)
- **Ответ `200` (`ReviewResponse`):**
  - `id`, `user_id`, `text`, `score`, `created_at`.

### `POST /reviews/organization/{org_id}`
- **Доступ:** авторизованный пользователь.
- **Тело/ответ:** те же, что для клуба (`ReviewCreate` → `ReviewResponse`).

---

## Ratings (`/ratings`)

### `GET /ratings/club/{club_id}`
- **Доступ:** публичный.
- **Ответ `200` (`RatingResponse`):**
  - `avg_score` (Decimal)
  - `review_count` (int)

### `GET /ratings/organization/{org_id}`
- **Доступ:** публичный.
- **Ответ `200` (`RatingResponse`).

---

## Search (`/search`)

### `GET /search/health`
- **Доступ:** публичный.
- **Ответ `200` (`SearchHealthResponse`):**
  - `qdrant_reachable`
  - `collection_exists`
  - `embedding_model`
  - `personalization_enabled`
  - `tracked_events_last_24h`
  - `last_profile_build`
  - `last_error`

### `POST /search/reindex`
- **Доступ:** публичный (в коде ограничений нет).
- **Тело:** нет.
- **Ответ `200` (`ReindexResponse`):**
  - `indexed` (int)

### `POST /search/click`
- **Доступ:** только авторизованный пользователь.
- **Тело (JSON, `SearchClickRequest`):**
  - `doc_id` (string, обязательно)
  - `position` (int | null)
  - `query_text` (string | null)
- **Ответ `200` (`SearchClickResponse`):**
  - `ok` (bool)

### `GET /search/recommend`
- **Доступ:** только авторизованный пользователь.
- **Query params:**
  - `top_k` (int, 1..50, default 10)
  - `type` (`club | campaign | news`, опционально)
- **Ответ `200` (`SearchResponse`):**
  - `total` (int)
  - `items` (массив `SearchHit`): `type`, `entity_id`, `title`, `snippet`, `url`, `score`

### `GET /search`
- **Доступ:** публичный (с токеном включает персонализацию/трекинг).
- **Query params:**
  - `q` (string, min_length=2, обязательно)
  - `top_k` (int, 1..50, default 10)
  - `type` (`club | campaign | news`, опционально)
  - `city` (опционально)
  - `category` (опционально)
  - `status` (опционально)
  - `role_boost` (bool, default `true`)
  - `track` (bool | null)
- **Ответ `200` (`SearchResponse`)** с массивом `SearchHit`.

---

## Enum-значения, которые важно учитывать

- `UserRole`: `member`, `club`, `organization`, `investor`
- `CampaignStatus`: `draft`, `active`, `finished`, `canceled`
- `InvestmentStatus`: `pending`, `paid`, `canceled`
- `FundingType`: `donation`, `investment`, `sponsorship`
- `PaymentProvider`: `paybox`, `stripe`
- `PaymentStatus`: `created`, `pending`, `success`, `failed`, `canceled`, `refunded`
- `CompetitionStatus`: `draft`, `active`, `finished`, `canceled`

