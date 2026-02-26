# Таблицы базы данных (подробное описание)

Документ собран по SQLAlchemy-моделям проекта.

## 1) Пользователи и профильные сущности

### `users`
Базовая таблица всех типов аккаунтов (обычный пользователь, клуб, организация, инвестор).

- **Ключевые поля**:
  - `id` — PK.
  - `email` — уникальный email, индекс.
  - `hashed_password` — хэш пароля.
  - `role` — ENUM `user_role` (`member`, `club`, `organization`, `investor`), индекс.
  - `avatar_key` — путь/ключ аватара в хранилище.
  - `is_active` — флаг активности.
  - `created_at`, `updated_at` — метки времени.
- **Назначение**: единая точка аутентификации и авторизации.
- **Особенность**: полиморфная база для дочерних таблиц `clubs`, `organizations`, `investors`.

### `clubs`
Профиль клуба (дочерняя таблица от `users`).

- **Ключевые поля**:
  - `id` — PK и FK → `users.id`.
  - `name`, `category`, `city`, `description`.
  - `edu_org_id` — FK → `educational_organizations.id`.
  - `logo_key`, `website`, `social_links` (JSON).
- **Связи**:
  - 1:N с `campaigns`, `news`, `competitions`, `club_reviews`.
  - 1:1 с `club_ratings`.
  - N:1 с `educational_organizations`.

### `organizations`
Профиль организации (дочерняя таблица от `users`).

- **Ключевые поля**:
  - `id` — PK и FK → `users.id` (CASCADE).
  - `name`, `city`, `description`, `logo_key`, `website`.
- **Связи**:
  - 1:N с `organization_reviews`.
  - 1:1 с `organization_ratings`.

### `investors`
Профиль инвестора (дочерняя таблица от `users`).

- **Ключевые поля**:
  - `id` — PK и FK → `users.id` (CASCADE).
  - `bio`, `company_name`, `linkedin_url`.
- **Связи**:
  - 1:N с `investments`.

### `educational_organizations`
Справочник учебных организаций, к которым могут быть привязаны клубы.

- **Ключевые поля**:
  - `id` — PK.
  - `name`, `city` (индекс), `departments` (JSON), `description`.
  - `logo_key`, `website`, `social_links` (JSON).
  - `created_at`, `updated_at`.
- **Связи**:
  - 1:N с `clubs`.

---

## 2) Фандрайзинг и платежи

### `campaigns`
Кампания клуба по сбору средств.

- **Ключевые поля**:
  - `id` — PK.
  - `club_id` — FK → `clubs.id` (CASCADE), индекс.
  - `title`, `description`, `goal_amount` (`Numeric(14,2)`).
  - `starts_at`, `ends_at`.
  - `status` — ENUM `campaign_status` (`draft`, `active`, `finished`, `canceled`), индекс.
  - `cover_key`, `gallery_keys` (PostgreSQL ARRAY).
  - `created_at`, `updated_at`.
- **Ограничения**:
  - `ends_at > starts_at`.
  - `goal_amount > 0`.
- **Связи**:
  - N:1 к `clubs`.
  - 1:N к `investments`.

### `investments`
Вклад/инвестиция пользователя-инвестора в кампанию.

- **Ключевые поля**:
  - `id` — PK.
  - `campaign_id` — FK → `campaigns.id` (`RESTRICT`), индекс.
  - `investor_id` — FK → `investors.id` (CASCADE), индекс.
  - `amount` (`Numeric(14,2)`).
  - `type` — ENUM `funding_type` (`donation`, `investment`, `sponsorship`).
  - `status` — ENUM `investment_status` (`pending`, `paid`, `canceled`), индекс.
  - `paid_at`, `created_at`, `updated_at`.
- **Ограничение**:
  - `amount > 0`.
- **Связи**:
  - N:1 к `campaigns`.
  - N:1 к `investors`.
  - 1:1 к `payments`.

### `payments`
Платежная сущность по конкретной инвестиции.

- **Ключевые поля**:
  - `id` — PK.
  - `investment_id` — FK → `investments.id` (CASCADE), уникальный, индекс.
  - `provider` — ENUM `payment_provider` (`paybox`, `stripe`).
  - `provider_payment_id`, `checkout_url`.
  - `amount` (`Numeric(14,2)`).
  - `status` — ENUM `payment_status` (`created`, `pending`, `success`, `failed`, `canceled`, `refunded`).
  - `idempotency_key`, `last_event_at`, `version`, `confirmed_at`.
  - `created_at`, `updated_at`.
- **Ограничения/индексы**:
  - UNIQUE (`provider`, `provider_payment_id`).
  - индекс (`status`, `created_at`).
- **Связи**:
  - 1:1 к `investments`.
  - 1:N к `payment_state_transition_logs`.

### `payment_idempotency`
Лог идемпотентности API-операций оплаты.

- **Ключевые поля**:
  - `id` — PK.
  - `user_id` — FK → `users.id` (CASCADE), индекс.
  - `scope`, `idempotency_key`, `request_hash`.
  - `payment_id` — FK → `payments.id` (CASCADE).
  - `response_code`, `response_body` (JSON), `created_at`.
- **Ограничение**:
  - UNIQUE (`user_id`, `scope`, `idempotency_key`).

### `webhook_events`
Хранилище входящих webhook-событий от платежного провайдера.

- **Ключевые поля**:
  - `id` — PK.
  - `provider`, `provider_event_id`, `event_type`.
  - `signature_valid`.
  - `payload` (JSON), `payload_hash`.
  - `received_at`, `processed_at`.
  - `status` — ENUM `webhook_event_status` (`received`, `processed`, `ignored`, `failed`).
  - `error_message`.
- **Ограничения/индексы**:
  - UNIQUE (`provider`, `provider_event_id`).
  - UNIQUE (`provider`, `payload_hash`).
  - индекс (`status`, `received_at`).
- **Связи**:
  - 1:N к `webhook_delivery_logs`.

### `webhook_delivery_logs`
Журнал попыток обработки/доставки webhook-событий.

- **Ключевые поля**:
  - `id` — PK.
  - `webhook_event_id` — FK → `webhook_events.id` (CASCADE), индекс.
  - `attempt_no`.
  - `http_headers` (JSON), `remote_addr`.
  - `processed`, `http_status`, `error`, `created_at`.
- **Ограничение**:
  - UNIQUE (`webhook_event_id`, `attempt_no`).

### `payment_state_transition_logs`
Аудит переходов статусов платежа.

- **Ключевые поля**:
  - `id` — PK.
  - `payment_id` — FK → `payments.id` (CASCADE), индекс.
  - `from_status`, `to_status` — ENUM `payment_status`.
  - `reason`.
  - `actor_type` — ENUM `payment_actor_type` (`system`, `user`, `webhook`).
  - `actor_id`, `created_at`.
- **Индекс**:
  - (`payment_id`, `created_at`).

---

## 3) Контент, активности и вовлечение

### `news`
Новости клубов.

- **Ключевые поля**:
  - `id` — PK.
  - `club_id` — FK → `clubs.id` (CASCADE), индекс.
  - `title`, `body`, `cover_key`.
  - `published_at`, `is_published`.
  - `created_at`, `updated_at`.
- **Индекс**:
  - (`club_id`, `is_published`).

### `competitions`
Соревнования/конкурсы, создаваемые клубами.

- **Ключевые поля**:
  - `id` — PK.
  - `club_id` — FK → `clubs.id` (CASCADE), индекс.
  - `title`, `description`.
  - `starts_at`, `ends_at`, `photo_key`.
  - `status` — ENUM `competition_status` (`draft`, `active`, `finished`, `canceled`).
  - `created_at`, `updated_at`.
- **Индекс**:
  - (`starts_at`, `ends_at`).
- **Связи**:
  - 1:N к `competition_subscriptions`.

### `competition_subscriptions`
Подписки пользователей на соревнования.

- **Ключевые поля**:
  - `id` — PK.
  - `competition_id` — FK → `competitions.id` (CASCADE), индекс.
  - `user_id` — FK → `users.id` (CASCADE), индекс.
  - `created_at`, `updated_at`.
- **Ограничение**:
  - UNIQUE (`competition_id`, `user_id`) — нельзя подписаться дважды.

### `club_reviews`
Отзывы пользователей о клубах.

- **Ключевые поля**:
  - `id` — PK.
  - `club_id` — FK → `clubs.id` (CASCADE).
  - `user_id` — FK → `users.id` (CASCADE).
  - `text`, `score` (1..5), `is_approved`.
  - `moderation_status`, `toxicity_score`, `moderation_labels` (JSON).
  - `created_at`, `updated_at`.
- **Ограничения**:
  - UNIQUE (`club_id`, `user_id`).
  - `score` в диапазоне 1..5.

### `organization_reviews`
Отзывы пользователей об организациях.

- **Ключевые поля**:
  - `id` — PK.
  - `organization_id` — FK → `organizations.id` (CASCADE).
  - `user_id` — FK → `users.id` (CASCADE).
  - `text`, `score` (1..5), `is_approved`.
  - `moderation_status`, `toxicity_score`, `moderation_labels` (JSON).
  - `created_at`, `updated_at`.
- **Ограничения**:
  - UNIQUE (`organization_id`, `user_id`).
  - `score` в диапазоне 1..5.

### `club_ratings`
Агрегированный рейтинг клуба.

- **Ключевые поля**:
  - `id` — PK.
  - `club_id` — FK → `clubs.id` (CASCADE), UNIQUE.
  - `avg_score` (`Numeric(3,2)`), `review_count`.
  - `created_at`, `updated_at`.

### `organization_ratings`
Агрегированный рейтинг организации.

- **Ключевые поля**:
  - `id` — PK.
  - `organization_id` — FK → `organizations.id` (CASCADE), UNIQUE.
  - `avg_score` (`Numeric(3,2)`), `review_count`.
  - `created_at`, `updated_at`.

---

## 4) Поиск и аналитика

### `search_events`
События поисковых запросов.

- **Ключевые поля**:
  - `id` — PK.
  - `user_id` — FK → `users.id` (CASCADE), nullable, индекс.
  - `query_text`, `role`.
  - `filters_json` (JSON), `top_doc_ids` (JSON).
  - `created_at`.
- **Назначение**:
  - аналитика качества поиска и персонализация.

### `click_events`
События кликов по результатам поиска.

- **Ключевые поля**:
  - `id` — PK.
  - `user_id` — FK → `users.id` (CASCADE), индекс.
  - `doc_id`, `doc_type`, `entity_id`, `position`, `query_text`.
  - `created_at`.
- **Назначение**:
  - обучение ранжирования, CTR-аналитика.

### `user_search_profiles`
Агрегированный профиль интересов пользователя для персонализации поиска.

- **Ключевые поля**:
  - `user_id` — PK и FK → `users.id` (CASCADE).
  - `top_cities`, `top_categories`, `top_types` (JSON-массивы).
  - `updated_at`.

---

## Краткая карта зависимостей

- Наследование: `users` → (`clubs`, `organizations`, `investors`).
- Клубы: `clubs` → (`campaigns`, `news`, `competitions`, `club_reviews`, `club_ratings`).
- Фандрайзинг: `campaigns` → `investments` → `payments`.
- Платежные логи: `payments` → `payment_state_transition_logs`; `webhook_events` → `webhook_delivery_logs`; `payment_idempotency` связывает пользователя и платеж.
- Репутация: `club_reviews` → `club_ratings`; `organization_reviews` → `organization_ratings`.
- Поиск: `search_events`, `click_events`, `user_search_profiles` опираются на `users`.

