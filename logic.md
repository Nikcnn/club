Ниже — разбор как устроена логика в services-слое в целом, и отдельно подробно по search и moderation.
1) Общая логика services в проекте

    В проекте используется типичный паттерн: роуты (FastAPI) тонкие, а бизнес-операции вынесены в сервис-классы (*Service) со @staticmethod. Это видно, например, в users/routes.py: роут проверяет входные условия и вызывает UserService (get_by_email, create_member, authenticate).

    Сервисы работают напрямую с AsyncSession SQLAlchemy: формируют select, делают db.add, commit, refresh, возвращают доменные объекты. Это стандартный стиль во многих модулях (users, clubs, reviews и т.д.).

    Важный момент: сервисы не только CRUD, но и оркестрация между доменами. Например, при создании/обновлении клуба сервис сразу синхронизирует поисковый индекс (SearchService.upsert_single).

    В main.py подключены все роутеры, а для поиска на старте приложения вызывается ensure_collection() в lifespan — то есть поиск поднимается как инфраструктурная часть при старте API.

2) Логика search: как работает end-to-end
2.1 API-уровень (apps/search/routes.py)

    Есть ключевые endpoints:

        /search/health — проверка состояния Qdrant + метрики трекинга.

        /search/reindex — полная переиндексация.

        /search — семантический поиск с фильтрами и optional персонализацией.

        /search/click — логирование клика (только для авторизованного).

        /search/recommend — рекомендации по профилю кликов пользователя с fallback-режимом.

    Авторизация в поиске гибкая:

        get_optional_current_user пытается распарсить access JWT, но не ломает запрос, если токен невалидный/отсутствует.

        Для /click и /recommend используется строгий get_required_current_user (401 при отсутствии пользователя).

2.2 Индексация (SearchService.rebuild_index)

    Сервис собирает документы из трех сущностей: Club, Campaign, News.

    Для каждой сущности строится payload (type, entity_id, title, snippet, url, и метаданные фильтрации).

    Текст для эмбеддинга формируется из значимых полей (title/snippet/city/category/status).

    Далее идет векторизация через SentenceTransformer и upsert в Qdrant c детерминированным doc_id (UUID5 от type:entity_id).

2.3 Поиск (semantic_search)

    Перед поиском проверяется доступность коллекции (ensure_collection), иначе 503.

    Текст запроса переводится в вектор.

    Фильтры (type/city/category/status) собираются в Qdrant Filter.

    Выполняется vector search (search_points) и нормализация результатов к API-формату.

    Дополнительно накладывается _city_query_precision_filter (если указан city): приоритет точной фразы, затем все токены, затем эвристика по ближайшему числу (полезно для запросов вида “222”).

2.4 Персонализация и рекомендации

    В /search персонализация включается только если:

        в конфиге PERSONALIZATION_ENABLED=True,

        пользователь авторизован.

    Предпочтения считаются из последних кликов (doc_type/city/category) через compute_user_preferences.

    Затем rerank_results добавляет бонусы:

        за соответствие роли пользователя,

        за совпадение города/категории/типа,

        за частоту кликов по типу контента (малый bias).

    Для /recommend:

        берутся последние клики,

        восстанавливаются doc_id для Qdrant,

        вытягиваются вектора clicked-доков,

        строится усредненный профильный вектор (с нормализацией),

        делается recommendation search с исключением уже кликнутых doc_id.

        если профиля нет — fallback: инвесторам/по campaign возвращаются активные кампании, иначе клубы.

2.5 Tracking/аналитика поиска

    Логируется:

        SearchEvent (запрос, фильтры, top doc_ids, роль),

        ClickEvent (doc_id/doc_type/entity_id/позиция/query).

    log_search_event безопасно обрабатывает ошибки записи (rollback + warning, но не валит ответ пользователю).

    Есть счетчик событий за 24 часа для health-эндпоинта.

2.6 Устойчивость инфраструктуры поиска

    Qdrant-клиент singleton-подобный (get_qdrant_client), состояние доступности держится в qdrant_state.

    ensure_collection создает коллекцию при отсутствии, обновляет флаги reachable/last_error.

    При недоступности Qdrant возвращается degraded mode (например, 503 в search/reindex).

3) Логика moderation

    Модерация реализована в ModerationService как асинхронный провайдер-агностичный слой (сейчас поддержан openrouter).

    Процесс analyze_text:

        Проверка фич-флага MODERATION_ENABLED.

        Проверка провайдера (openrouter) и API key.

        Запрос в LLM с жесткой системной инструкцией вернуть JSON (toxicity_score, labels, reason).

        Нормализация формата контента (строка/список/словарь).

        Парсинг JSON даже из fenced code block.

        Clamp toxicity_score в диапазон [0..1], сбор labels/reason.

        При ошибках — fallback-режим.

    decide_status переводит токсичность в бизнес-статус:

        >= TOXICITY_THRESHOLD_REJECT → REJECTED, is_approved=False;

        >= TOXICITY_THRESHOLD_PENDING → PENDING, is_approved=False;

        иначе APPROVED, is_approved=True.

    Fallback-логика зависит от MODERATION_FAIL_MODE:

        "pending" → принудительно pending,

        иначе approve-by-default (0.0, fallback=approve).

4) Как moderation связана с reviews (практический поток)

    При создании отзыва (club/organization) сервис:

        Проверяет, что пользователь еще не оставлял отзыв на объект.

        Вызывает ModerationService.analyze_text.

        Вызывает decide_status и пишет toxicity_score, moderation_labels, moderation_status, is_approved.

        Пересчитывает рейтинг только если отзыв approved.

    Публичные листинги отзывов отдают только is_approved=True (pending/rejected не видны).

    Это отражено и в модели отзывов: есть поля moderation и enum-статусы (PENDING/APPROVED/REJECTED).

    И покрыто тестами: проверяется корректная установка статуса и условный пересчет рейтинга, а также фильтрация только approved в публичных выдачах.
