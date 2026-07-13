# API Reference — AI Roleplay Coach Hub

> **Версия:** 1.0.0  
> **Статус:** Production-ready MVP  
> **Последнее обновление:** 2026-07-12  
> **Назначение:** Полный справочник REST API — эндпоинты, модели запросов/ответов, аутентификация, RBAC, ограничение запросов, HTTP-ошибки, примеры.

---

## Содержание

- [1. Основная информация](#1-основная-информация)
  - [1.1. Базовый URL](#11-базовый-url)
  - [1.2. Аутентификация (JWT Bearer)](#12-аутентификация-jwt-bearer)
  - [1.3. Роли и RBAC](#13-роли-и-rbac)
  - [1.4. Формат ошибок (RFC 9457)](#14-формат-ошибок-rfc-9457)
  - [1.5. Пагинация](#15-пагинация)
- [2. Аутентификация (/api/v1/auth)](#2-аутентификация-apiv1auth)
  - [2.1. POST /register](#21-post-register)
  - [2.2. POST /login](#22-post-login)
  - [2.3. POST /refresh](#23-post-refresh)
  - [2.4. POST /logout](#24-post-logout)
  - [2.5. GET /me](#25-get-me)
  - [2.6. GET /users](#26-get-users)
- [3. Сессии (/api/v1/sessions)](#3-сессии-apiv1sessions)
  - [3.1. POST /sessions](#31-post-sessions)
  - [3.2. GET /sessions](#32-get-sessions)
  - [3.3. GET /sessions/{id}](#33-get-sessionsid)
  - [3.4. POST /sessions/{id}/turns](#34-post-sessionsidturns)
  - [3.5. POST /sessions/{id}/finish](#35-post-sessionsidfinish)
  - [3.6. POST /sessions/{id}/evaluate](#36-post-sessionsidevaluate)
- [4. Simulator API (/api/v1/simulator)](#4-simulator-api-apiv1simulator)
  - [4.1. POST /simulator/start](#41-post-simulatorstart)
  - [4.2. POST /simulator/respond](#42-post-simulatorrespond)
  - [4.3. POST /simulator/should-end/{session_id}](#43-post-simulatorshould-endsession_id)
- [5. Coach API (/api/v1/coach)](#5-coach-api-apiv1coach)
  - [5.1. POST /coach/evaluate](#51-post-coachevaluate)
- [6. Curator API (/api/v1/curator)](#6-curator-api-apiv1curator)
  - [6.1. POST /curator/learning-plan](#61-post-curatorlearning-plan)
  - [6.2. POST /curator/quiz](#62-post-curatorquiz)
  - [6.3. POST /curator/sync-lms](#63-post-curatorsync-lms)
- [7. Геймификация (/api/v1/gamification)](#7-геймификация-apiv1gamification)
  - [7.1. GET /gamification/xp/{user_id}](#71-get-gamificationxpid)
  - [7.2. GET /gamification/xp/{user_id}/history](#72-get-gamificationxpidhistory)
  - [7.3. GET /gamification/badges](#73-get-gamificationbadges)
  - [7.4. GET /gamification/badges/{user_id}](#74-get-gamificationbadgesid)
  - [7.5. GET /gamification/leaderboard](#75-get-gamificationleaderboard)
  - [7.6. GET /gamification/streak/{user_id}](#76-get-gamificationstreakid)
- [8. Аналитика и Fairness (/api/v1/analyst)](#8-аналитика-и-fairness-apiv1analyst)
  - [8.1. GET /analyst/stats](#81-get-analyststats)
  - [8.2. GET /analyst/stats/{user_id}](#82-get-analyststatsuser_id)
  - [8.3. GET /analyst/distribution/{user_id}](#83-get-analystdistributionuser_id)
  - [8.4. GET /analyst/progress/{user_id}](#84-get-analystprogressuser_id)
  - [8.5. GET /analyst/fairness/report](#85-get-analystfairnessreport)
  - [8.6. GET /analyst/fairness/groups](#86-get-analystfairnessgroups)
  - [8.7. GET /analyst/fairness/history](#87-get-analystfairnesshistory)
- [9. Health и метрики](#9-health-и-метрики)
  - [9.1. GET /health](#91-get-health)
  - [9.2. GET /ready](#92-get-ready)
  - [9.3. GET /api/v1/metrics](#93-get-apiv1metrics)
- [10. HTTP-коды ошибок](#10-http-коды-ошибок)
- [11. Ограничение запросов](#11-ограничение-запросов)
- [12. WebSocket (планируется)](#12-websocket-планируется)
- [13. Сводная таблица маршрутов](#13-сводная-таблица-маршрутов)


---

## 1. Основная информация

### 1.1. Базовый URL

```
http://localhost:8000
```

Все маршруты API (кроме health/metrics) используют префикс /api/v1.

### 1.2. Аутентификация (JWT Bearer)

Защищённые эндпоинты требуют:

```
Authorization: Bearer <access_token>
```

Токены:
- **Access token** — короткоживущий (15 мин по умолчанию), отправляется с каждым запросом.
- **Refresh token** — долгоживущий (7 дней), используется только для /auth/refresh.

Настройки JWT задаются через переменные окружения: JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_REFRESH_EXPIRE_DAYS.
См.: [src/core/config.py](../src/core/config.py)

### 1.3. Роли и RBAC

| Роль | Разрешения |
|------|------------|
| OPERATOR | Базовые: создание/запуск сессий, просмотр своих результатов и геймификации |
| TRAINER | Просмотр статистики и аналитики, оценка сессий, создание квизов |
| ADMIN | Полный доступ: управление пользователями, Fairness-аудит, синхронизация с LMS, все данные |

RBAC через зависимость require_role(): [src/api/dependencies.py](../src/api/dependencies.py#L265)

**Примечание:** ADMIN имеет универсальный обход — проходит любую проверку роли (строки 250-254).

### 1.4. Формат ошибок (RFC 9457)

Все ошибки используют формат Problem Details:

```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "Session not found",
  "instance": "http://localhost:8000/api/v1/sessions/123"
}
```

Обработчики ошибок: [src/main.py](../src/main.py#L288)

### 1.5. Пагинация

Эндпоинты со списками используют стандартный формат пагинации.

**Параметры запроса:**
| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| page | int | 1 | Номер страницы |
| size | int | 20 | Элементов на странице |

**Формат ответа:**

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 20
}
```

Реализация: [src/core/dto/pagination.py](../src/core/dto/pagination.py)

---

## 2. Аутентификация (/api/v1/auth)

Роутер: [src/api/auth.py](../src/api/auth.py)

### 2.1. POST /register

Регистрация нового пользователя.

**Запрос:**
```json
{"username": "operator1", "password": "SecurePass123"}
```

**Ответ (201):**
```json
{"access_token": "<token>", "refresh_token": "<token>", "user_id": "uuid", "username": "operator1", "role": "operator"}
```

Ошибки: 409 Conflict (дубликат), 422 Ошибка валидации

### 2.2. POST /login

Аутентификация и получение пары токенов.

**Запрос:** `{"username": "...", "password": "..."}`

**Ответ (200):** Аналогично регистрации.

Ошибки: 401 Неверные учётные данные

### 2.3. POST /refresh

Обмен refresh-токена на новую пару токенов.

**Запрос:** `{"refresh_token": "<token>"}`

**Ответ (200):** Аналогично регистрации.

Ошибки: 401 Неверный/просроченный refresh-токен

### 2.4. POST /logout

Отзыв refresh-токена.

**Запрос:** `{"refresh_token": "<token>"}`

**Ответ (200):** `{"detail": "Logged out"}`

### 2.5. GET /me

Информация о текущем пользователе (требуется Bearer-токен).

**Ответ (200):**
```json
{"user_id": "uuid", "username": "operator1", "role": "operator", "email": "op1@example.com", "is_active": true}
```

Ошибки: 401 Отсутствует/неверный токен

### 2.6. GET /users

Список всех пользователей (только ADMIN). С пагинацией (page, size).

**Ответ (200):** Пагинированный список объектов UserInfo.

Ошибки: 403 Доступ запрещён (не ADMIN)

---

## 3. Сессии (/api/v1/sessions)

Роутер: [src/api/sessions.py](../src/api/sessions.py)

### 3.1. POST /sessions

Запуск новой симуляционной сессии.

**Запрос:** `{"scenario_id": "uuid"}`

**Ответ (201):** Объект Session (status=in_progress)

Ошибки: 404 Сценарий не найден

### 3.2. GET /sessions

Список сессий текущего пользователя. С пагинацией (page, size).

**Ответ (200):** Page[Session]

### 3.3. GET /sessions/{id}

Детали сессии по ID.

Ошибки: 404 Сессия не найдена

### 3.4. POST /sessions/{id}/turns

Обработка хода оператора.

**Запрос:** `{"user_id": "uuid", "message": "..."}`

Ошибки: 400 Сессия не найдена или не в статусе in_progress

### 3.5. POST /sessions/{id}/finish

Завершение сессии (status -> COMPLETED).

Ошибки: 400 Сессия не найдена или уже завершена

### 3.6. POST /sessions/{id}/evaluate

Оценка завершённой сессии (TRAINER/ADMIN).

**Ответ (200):** `{"session": {...}, "evaluation": {...}}`

Ошибки: 400 Не найдена/не завершена, 403 Доступ запрещён

---

## 4. Simulator API (/api/v1/simulator)

Роутер: [src/api/simulator.py](../src/api/simulator.py)
Автономные эндпоинты SimulatorAgent (без сохранения сессии).

### 4.1. POST /simulator/start

Запуск автономного диалога.

**Запрос:** `{"scenario_id": "uuid"}`

**Ответ (200):** `{"greeting": "...", "psychotype": "..."}`

Ошибки: 404 Сценарий не найден

### 4.2. POST /simulator/respond

Генерация ответа клиента для сессии.

**Запрос:** `{"session_id": "uuid"}`

**Ответ (200):** `{"client_message": "..."}`

Ошибки: 404 Сессия не найдена

### 4.3. POST /simulator/should-end/{session_id}

Проверка, должен ли диалог завершиться.

**Ответ (200):** `{"should_end": false}`

Ошибки: 404 Сессия не найдена

---

## 5. Coach API (/api/v1/coach)

Роутер: [src/api/coach.py](../src/api/coach.py)
Автономная оценка (без сохранения).

### 5.1. POST /coach/evaluate

Независимая оценка сессии.

**Запрос:** `{"session_id": "uuid"}`

**Ответ (200):** Объект оценки с overall_score, 5 подоценками, praise/growth/closing текстом.

Ошибки: 404 Сессия/сценарий не найдены, 500 Ошибка Coach

---

## 6. Curator API (/api/v1/curator)

Роутер: [src/api/curator.py](../src/api/curator.py)

### 6.1. POST /curator/learning-plan

Генерация учебного плана. Любая роль.

**Запрос:** `{"scenario_id": "uuid"}`

**Ответ (200):** Объект LearningPlan

Ошибки: 404 Сценарий не найден, 400 Ошибка Curator

### 6.2. POST /curator/quiz

Генерация микро-квиза (TRAINER/ADMIN).

**Запрос:** `{"scenario_id": "uuid", "question_count": 5}`

**Ответ (200):** Квиз с вопросами/вариантами/correct_index

Ошибки: 404 Сценарий не найден

### 6.3. POST /curator/sync-lms

Заглушка: синхронизация учебного плана с LMS (только ADMIN).

**Запрос:** `{"plan_id": "uuid"}`

**Ответ (200):** `{"status": "synced", "lms_course_id": "...", "lms_url": "...", "plan_id": "..."}`

---

## 7. Геймификация (/api/v1/gamification)

Роутер: [src/api/gamification.py](../src/api/gamification.py)

### 7.1. GET /gamification/xp/{user_id}

Баланс XP и уровень.

**Ответ (200):** `{"xp_total": 2500, "level": 2, "xp_to_next_level": 500}`

Ошибки: 404 Пользователь не найден

### 7.2. GET /gamification/xp/{user_id}/history

История транзакций XP (с пагинацией).

**Ответ (200):** Page элементов {id, amount, reason, reference_id, created_at}

### 7.3. GET /gamification/badges

Список всех доступных значков.

### 7.4. GET /gamification/badges/{user_id}

Значки, полученные пользователем. Ошибки: 404 Пользователь не найден

### 7.5. GET /gamification/leaderboard

Топ пользователей по XP (с пагинацией).

### 7.6. GET /gamification/streak/{user_id}

Текущая серия. Ошибки: 404 Пользователь не найден

---

## 8. Аналитика и Fairness (/api/v1/analyst)

Роутер: [src/api/analyst.py](../src/api/analyst.py)

### 8.1. GET /analyst/stats

Глобальная статистика платформы (TRAINER/ADMIN).

### 8.2. GET /analyst/stats/{user_id}

Статистика для конкретного пользователя.

### 8.3. GET /analyst/distribution/{user_id}

Гистограмма распределения оценок по каждому измерению.

### 8.4. GET /analyst/progress/{user_id}

Временной ряд общих оценок. Параметр: limit (1-100, по умолчанию 20).

### 8.5. GET /analyst/fairness/report

Генерация отчёта Fairness (только ADMIN). Параметр: scenario_id (необязательно).

### 8.6. GET /analyst/fairness/groups

Список защищённых атрибутов (только ADMIN).

### 8.7. GET /analyst/fairness/history

История отчётов (только ADMIN). Кольцевой буфер в памяти, макс. 100. Параметры: skip, limit.

---

## 9. Health и метрики

### 9.1. GET /health

Проверка живости (без аутентификации).

**Ответ (200):** `{"status": "ok", "version": "0.1.0", "uptime_seconds": 3600}`

### 9.2. GET /ready

Проверка готовности (без аутентификации).

**Ответ (200):** `{"status": "ok", "version": "0.1.0", "uptime_seconds": 3600, "components": {"auth": "ok", ...}}`

### 9.3. GET /api/v1/metrics

Метрики Prometheus в текстовом формате (без аутентификации, для внутренних сборщиков).

Метрики, собираемые MetricsMiddleware:
- http_requests_total (Counter: method, path, status)
- http_request_duration_seconds (Histogram: method, path)
- active_sessions (Gauge)
- total_evaluations (Counter)
- circuit_breaker_state (Gauge: circuit)

Эндпоинт: [src/api/metrics.py](../src/api/metrics.py#L55)
Middleware: [src/api/metrics.py](../src/api/metrics.py#L64)

---

## 10. HTTP-коды ошибок

| Код | Название | Причина |
|-----|----------|---------|
| 400 | Bad Request | Неверные параметры, нарушение бизнес-правил |
| 401 | Unauthorized | Отсутствует или неверен токен |
| 403 | Forbidden | У роли нет доступа |
| 404 | Not Found | Ресурс не найден |
| 409 | Conflict | Дубликат имени пользователя |
| 422 | Validation Error | Ошибка валидации Pydantic |
| 429 | Too Many Requests | Превышен лимит запросов |
| 500 | Internal Server Error | Необработанная ошибка сервера |

---

## 11. Ограничение запросов

Два уровня ограничения запросов:

### 11.1. Общий RateLimitMiddleware

[src/api/rate_limit.py](../src/api/rate_limit.py)

| Тип | Путь | Лимит | Окно |
|-----|------|-------|------|
| По умолчанию | Все, кроме /metrics, /health, /ready | 100 | 60s |
| Auth | /api/v1/auth/* | 10 | 60s |

Заголовки ответа: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

### 11.2. AuthRateLimitMiddleware

[src/api/auth_rate_limit_middleware.py](../src/api/auth_rate_limit_middleware.py)

| Путь | Лимит | Окно | Блокировка |
|------|-------|------|------------|
| /api/v1/auth/register | 5 | 600s | 1800s |
| /api/v1/auth/login | 10 | 600s | 1800s |
| /api/v1/auth/refresh | 20 | 600s | 1800s |
| /api/v1/auth (запасной) | 20 | 600s | 1800s |

---

## 12. WebSocket (планируется)

> **Статус:** Планируется / Roadmap. Не реализовано в текущей версии.

Спецификация: ws://host:8000/api/v1/ws/session/{session_id}

Формат JSON-сообщений. События: session_started, operator_message, client_message, session_completed, error.

Roadmap: [docs/ARCHITECTURE_ROADMAP.md](../docs/ARCHITECTURE_ROADMAP.md)

---

## 13. Сводная таблица маршрутов

### REST API

| Метод | Путь | Аутентификация | Роль |
|-------|------|----------------|------|
| POST | /api/v1/auth/register | Нет | -- |
| POST | /api/v1/auth/login | Нет | -- |
| POST | /api/v1/auth/refresh | Нет | -- |
| POST | /api/v1/auth/logout | Bearer | Любая |
| GET | /api/v1/auth/me | Bearer | Любая |
| GET | /api/v1/auth/users | Bearer | ADMIN |
| POST | /api/v1/sessions | Bearer | OP/TRAINER/ADMIN |
| GET | /api/v1/sessions | Bearer | Любая |
| GET | /api/v1/sessions/{id} | Bearer | Любая |
| POST | /api/v1/sessions/{id}/turns | Bearer | Любая |
| POST | /api/v1/sessions/{id}/finish | Bearer | Любая |
| POST | /api/v1/sessions/{id}/evaluate | Bearer | TRAINER/ADMIN |
| POST | /api/v1/simulator/start | Bearer | Любая |
| POST | /api/v1/simulator/respond | Bearer | Любая |
| POST | /api/v1/simulator/should-end/{id} | Bearer | Любая |
| POST | /api/v1/coach/evaluate | Bearer | Любая |
| POST | /api/v1/curator/learning-plan | Bearer | Любая |
| POST | /api/v1/curator/quiz | Bearer | TRAINER/ADMIN |
| POST | /api/v1/curator/sync-lms | Bearer | ADMIN |
| GET | /api/v1/gamification/xp/{id} | Bearer | Любая |
| GET | /api/v1/gamification/xp/{id}/history | Bearer | Любая |
| GET | /api/v1/gamification/badges | Bearer | Любая |
| GET | /api/v1/gamification/badges/{id} | Bearer | Любая |
| GET | /api/v1/gamification/leaderboard | Bearer | Любая |
| GET | /api/v1/gamification/streak/{id} | Bearer | Любая |
| GET | /api/v1/analyst/stats | Bearer | TRAINER/ADMIN |
| GET | /api/v1/analyst/stats/{id} | Bearer | Любая |
| GET | /api/v1/analyst/distribution/{id} | Bearer | Любая |
| GET | /api/v1/analyst/progress/{id} | Bearer | Любая |
| GET | /api/v1/analyst/fairness/report | Bearer | ADMIN |
| GET | /api/v1/analyst/fairness/groups | Bearer | ADMIN |
| GET | /api/v1/analyst/fairness/history | Bearer | ADMIN |
| GET | /health | Нет | -- |
| GET | /ready | Нет | -- |
| GET | /api/v1/metrics | Нет | -- |

### Middleware (не эндпоинты)

| Middleware | Назначение | Файл |
|------------|------------|------|
| RequestIDMiddleware | Генерация/прокси X-Request-ID | [middleware.py](../src/api/middleware.py) |
| MetricsMiddleware | Метрики Prometheus | [metrics.py](../src/api/metrics.py#L64) |
| RateLimitMiddleware | Скользящее окно ограничения запросов | [rate_limit.py](../src/api/rate_limit.py) |
| AuthRateLimitMiddleware | Посегментное ограничение аутентификации | [auth_rate_limit_middleware.py](../src/api/auth_rate_limit_middleware.py) |
| SecurityHeadersMiddleware | HTTP-заголовки безопасности | [security_headers.py](../src/api/security_headers.py) |

---

## Источники

- [src/api/router.py](../src/api/router.py)
- [src/api/auth.py](../src/api/auth.py)
- [src/api/sessions.py](../src/api/sessions.py)
- [src/api/simulator.py](../src/api/simulator.py)
- [src/api/coach.py](../src/api/coach.py)
- [src/api/curator.py](../src/api/curator.py)
- [src/api/gamification.py](../src/api/gamification.py)
- [src/api/analyst.py](../src/api/analyst.py)
- [src/api/dependencies.py](../src/api/dependencies.py)
- [src/api/middleware.py](../src/api/middleware.py)
- [src/api/rate_limit.py](../src/api/rate_limit.py)
- [src/api/security_headers.py](../src/api/security_headers.py)
- [src/api/metrics.py](../src/api/metrics.py)
- [src/main.py](../src/main.py)
