# Project Structure — AI Roleplay Coach Hub

> **Цель:** Навигационная карта репозитория. Для новых членов команды, онбординг.
> **Аудитория:** Разработчики, DevOps, архитекторы.
> **Принцип:** Каждая директория — один уровень ответственности. Backend — Domain-Driven Design, Frontend — Feature-Sliced Design.

---

## 1. Обзор репозитория

```
ai-roleplay-coach-agent-local/
│
├── src/                    🟢 Backend (Python 3.12+, FastAPI)
│   ├── main.py             Точка входа FastAPI-приложения
│   ├── agents/             5 AI-агентов (Simulator, Coach, Curator, Gamification, Analyst)
│   ├── api/                FastAPI эндпоинты + middleware + rate limiting
│   ├── core/               Domain core (DDD): entities, services, interfaces, DTO
│   ├── infrastructure/     Внешние интеграции: DB, LLM, Redis, Qdrant, ASR/TTS, LiveKit
│   ├── monitoring/         Prometheus-метрики (заглушка)
│   └── security/           Vault/HSM-интеграции (заглушка)
│
├── frontend/               🔵 Frontend (React 18, TypeScript, Vite, Tailwind)
│   └── src/                Feature-Sliced Design
│
├── tests/                  🧪 pytest (460+ тестов)
│   ├── api/                HTTP-тесты (FastAPI TestClient)
│   ├── unit/               Юнит-тесты агентов и сервисов
│   ├── integration/        Интеграционные тесты
│   ├── e2e/                Сквозные сценарии
│   └── security/           SAST-базовые проверки
│
├── docs-all/               📚 Новая полная документация (17 документов)
│   ├── README.md           Round 1 — Точка входа
│   ├── SPECIFICATION.md    Round 2 — Полная спецификация
│   ├── API.md              Round 3 — REST API справочник
│   └── PROJECT_STRUCTURE.md Round 4 — ЭТОТ ФАЙЛ
│
├── .github/workflows/      ⚙️ GitHub Actions (CI + Security)
├── scripts/                🛠 Вспомогательные скрипты
├── docs/                   📚 Старая документация (legacy)
├── reviews/                📋 Отчёты production review
├── backups/                💾 Бэкапы (gitignored)
├── logs/                   📝 Логи (gitignored)
│
├── [docker-compose.dev.yml](docker-compose.dev.yml)  🐳 Docker Compose (dev)
├── [docker-compose.prod.yml](docker-compose.prod.yml) 🐳 Docker Compose (production)
├── [Dockerfile.dev](Dockerfile.dev)          🐳 Dev-сборка
├── [Dockerfile.prod](Dockerfile.prod)         🐳 Prod-сборка (multi-stage)
├── [Makefile](Makefile)                ⚡ Основные команды (test, lint, run)
├── [pyproject.toml](pyproject.toml)          📦 Python project config
├── alembic.ini             📦 Database migrations config
├── [.env.example](.env.example)            🔐 Пример переменных окружения
└── [.pre-commit-config.yaml](.pre-commit-config.yaml) 🔍 Pre-commit hooks
```

---

## 2. `src/` — Backend (Python)

### 2.1. Точка входа и конфигурация

| Файл | Назначение |
|------|------------|
| `[src/main.py](src/main.py)` | `create_app()`, lifespan (startup/shutdown), регистрация middleware |
| `[src/core/config.py](src/core/config.py)` | `class Settings` — все env-переменные (JWT, DB, LLM, Redis, Rate Limit) |

### 2.2. `[src/api/](src/api/)` — FastAPI слой

| Файл | Назначение |
|------|------------|
| `router.py` | Регистрация всех роутеров (auth, sessions, coach, curator, gamification, analyst) |
| `auth.py` | Регистрация, логин, refresh, logout, me, users list |
| `auth_rate_limit_middleware.py` | Per-endpoint rate limit для auth |
| `sessions.py` | CRUD сессий симуляции |
| `simulator.py` | Эндпоинты Simulator API (start, respond, should-end) |
| `coach.py` | Оценка диалога (evaluate) |
| `curator.py` | Learning Plan, Quiz, LMS sync |
| `gamification.py` | XP, бейджи, лидерборд, streak |
| `analyst.py` | Статистика, прогресс, fairness-аудит |
| `dependencies.py` | DI: `get_*` сервисы, `auth_required` (role-based) |
| `middleware.py` | RequestID + Metrics middleware |
| `metrics.py` | Prometheus middleware + endpoint |
| `rate_limit.py` | Sliding-window rate limiter |
| `security_headers.py` | CSP, HSTS, X-Frame-Options и др. |

### 2.3. `[src/agents/](src/agents/)` — AI Агенты

#### 2.3.1. Simulator Agent (rule-based)

| Файл | Назначение |
|------|------------|
| `simulator/agent.py` | Rule-based эмуляция клиента: 4 психотипа, 6-фазный диалог, DDA |

#### 2.3.2. Simulator LLM (LLM-адаптер)

| Файл | Назначение |
|------|------------|
| `simulator_llm/agent.py` | LLM-адаптер для симуляции (ollama → openai-compat) |
| `simulator_llm/adapter.py` | Преобразование контекста в промпт для LLM |

#### 2.3.3. Coach Agent

| Файл | Назначение |
|------|------------|
| `coach/agent.py` | 5-мерная оценка диалога + фидбек «сэндвич» |
| `coach/adapter.py` | Преобразование сессии в промпт оценки |
| `coach/llm_agent.py` | LLM-версия Coach (для внешних LLM) |

#### 2.3.4. Curator Agent

| Файл | Назначение |
|------|------------|
| `curator/agent.py` | Подбор сценария, генерация learning plan и quiz |

#### 2.3.5. Gamification Engine

| Файл | Назначение |
|------|------------|
| `gamification/engine.py` | XP, уровни (1–20), бейджи, лидерборды, streak, DDA |

#### 2.3.6. Analyst

| Файл | Назначение |
|------|------------|
| `analyst/service.py` | Метрики и статистика по сессиям |
| `analyst/fairness_service.py` | Fairness-аудит по полу, возрасту, акценту, родному языку |

#### 2.3.7. Agent Services

| Файл | Назначение |
|------|------------|
| `services/dda_state_service.py` | Dynamic Difficulty Adjustment — управление состоянием |
| `services/double_write_service.py` | Double-write для in-memory + PostgreSQL |

### 2.4. `[src/core/](src/core/)` — Domain Core (DDD)

#### 2.4.1. Entities

| Файл | Сущность |
|------|----------|
| `entities/user.py` | User |
| `entities/session.py` | Session |
| `entities/scenario.py` | Scenario |
| `entities/script_node.py` | ScriptNode |
| `entities/evaluation.py` | Evaluation |
| `entities/xp.py` | XPEntry |
| `entities/badge.py` | Badge |
| `entities/learning_plan.py` | LearningPlan |
| `entities/quiz.py` | Quiz |
| `entities/lms_sync_result.py` | LMSSyncResult |
| `entities/fairness.py` | FairnessReport, FairnessGroup |
| `entities/dda_state.py` | DDAState |
| `entities/weights.py` | CoachWeights |

#### 2.4.2. DTOs

| Файл | Назначение |
|------|------------|
| `dto/pagination.py` | Pagination request/response |
| `dto/problem_detail.py` | RFC 7807 Problem Details |
| `dto/fairness_dto.py` | Fairness DTO |

#### 2.4.3. Interfaces (Ports)

| Файл | Назначение |
|------|------------|
| `interfaces/repositories.py` | UserRepository, SessionRepository, ScenarioRepository, EvaluationRepository, XPRepository, BadgeRepository, LearningPlanRepository, QuizRepository, FairnessRepository |
| `interfaces/agents.py` | SimulatorAgent, CoachAgent, CuratorAgent, GamificationEngine, AnalystService |
| `interfaces/llm_provider.py` | LLMProvider interface |
| `interfaces/token_store.py` | TokenStore interface |

#### 2.4.4. Services

| Файл | Назначение |
|------|------------|
| `services/auth_service.py` | JWT creation/validation, password hashing |
| `services/session_service.py` | Session lifecycle management |
| `services/evaluation_service.py` | Evaluation logic |
| `services/circuit_breaker.py` | Circuit breaker для внешних вызовов |

#### 2.4.5. Прочее

| Файл | Назначение |
|------|------------|
| `utils.py` | Утилиты (datetime, хеши) |
| `config.py` | Settings class |

### 2.5. `[src/infrastructure/](src/infrastructure/)` — Внешние интеграции

| Директория | Функция | Статус |
|------------|---------|--------|
| `postgres/` | SQLAlchemy async + asyncpg, модели, миграции (Alembic), репозитории | ✅ Активно |
| `postgres/database.py` | Async engine + session factory | ✅ |
| `postgres/models/` | SQLAlchemy ORM модели | ✅ |
| `postgres/repositories/` | PostgreSQL-реализации репозиториев | ✅ |
| `postgres/mappers/` | Mappers: Entity ↔ ORM model | ✅ |
| `postgres/migrations/` | Alembic — скрипты миграций | ✅ |
| `redis/` | Redis token store | ✅ Активно |
| `redis/token_store.py` | RedisTokenStore (JWT blacklist) | ✅ |
| `llm/` | LLM provider implementations | ✅ Активно |
| `llm/factory.py` | LLM provider factory | ✅ |
| `llm/mock_provider.py` | Mock LLM (dev/testing) | ✅ |
| `llm/ollama_provider.py` | Ollama LLM provider | ✅ |
| `qdrant/` | Vector DB for RAG | ✅ Активно |
| `qdrant/client.py` | Qdrant client wrapper | ✅ |
| `qdrant/rag_service.py` | RAG service (semantic search) | ✅ |
| `memory/` | In-memory repositories (dev mode) | ✅ Активно |
| `memory/repositories.py` | In-memory реализации всех репозиториев | ✅ |
| `livekit/` | Voice pipeline (LiveKit) | 🔧 Частично |
| `livekit/echo_agent.py` | Voice echo agent | 🔧 |
| `livekit/asr_stub.py` | ASR-заглушка | 🔧 |
| `livekit/tts_stub.py` | TTS-заглушка | 🔧 |
| `asr/` | ASR интеграция | 📋 Планируется |
| `tts/` | TTS интеграция | 📋 Планируется |
| `minio/` | S3-хранилище | 📋 Планируется |
| `notification/` | Notification service | 📋 Планируется |
| `notification/stub.py` | Notification-заглушка | 🔧 |
| `vault/` | HashiCorp Vault | 📋 Планируется |
| `logging.py` | structlog конфигурация (json/console) | ✅ Активно |

### 2.6. `[src/monitoring/](src/monitoring/)` и `[src/security/](src/security/)`

- `[src/monitoring/__init__.py](src/monitoring/__init__.py)` — заглушка для Prometheus-метрик
- `[src/security/__init__.py](src/security/__init__.py)` — заглушка для Vault/HSM интеграций

---

## 3. `frontend/` — Frontend (React + TypeScript)

Стек: **React 18, TypeScript, Vite, Tailwind CSS, Zustand (state), Orval (API client), Feature-Sliced Design**.

### 3.1. `[frontend/src/app/](frontend/src/app/)`

| Файл | Назначение |
|------|------------|
| `index.tsx` | Точка входа |
| `router.tsx` | React Router config |
| `providers.tsx` | Context providers |
| `styles/` | Tailwind CSS стили |
| `manifest.json` | PWA manifest |

### 3.2. `[frontend/src/pages/](frontend/src/pages/)`

| Директория | Назначение |
|------------|------------|
| `login.tsx` | Страница входа |
| `register.tsx` | Страница регистрации |
| `operator/dashboard.tsx` | Панель оператора |
| `operator/session/` | UI сессии (чат) |
| `trainer/dashboard.tsx` | Панель тренера |
| `trainer/learning-plan.tsx` | Управление учебными планами |
| `trainer/quiz/` | Управление квизами |
| `admin/dashboard.tsx` | Панель администратора |
| `admin/fairness.tsx` | UI аудита fairness |

### 3.3. `[frontend/src/features/](frontend/src/features/)` (по доменам)

| Директория | Назначение |
|------------|------------|
| `auth/` | Вход, регистрация, выход |
| `session/` | Создание сессии, чат, шаг |
| `evaluation/` | Отображение результатов оценки |
| `curator/` | Учебные планы, квизы |
| `gamification/` | XP, бейджи, лидерборд |
| `fairness/` | Панель fairness |
| `admin/` | Управление пользователями |

Каждая фича содержит `api/` (API client) и `ui/` (React компоненты).

### 3.4. `[frontend/src/entities/](frontend/src/entities/)`

| Директория | Назначение |
|------------|------------|
| `user/` | Модель пользователя |
| `evaluation/` | Модель оценки |
| `gamification/` | Модели XP, Badge |
| `curator/` | Модели LearningPlan, Quiz |

### 3.5. Прочие директории

| Директория | Назначение |
|------------|------------|
| `shared/api/` | API client (axios + Orval) |
| `shared/lib/` | Утилитарные функции |
| `shared/ui/` | Общие UI-компоненты (кнопки, поля, модалки) |
| `store/` | Zustand store (authStore, sessionStore, metricsStore) |
| `hooks/` | Кастомные хуки (useAuth, useWebSocket) |
| `widgets/` | Составные виджеты (Admin, Curator, layout) |
| `test/` | Frontend-тесты |

---

## 4. `tests/` — Тестовый набор (460+ тестов)

| Директория | Кол-во | Назначение |
|------------|--------|------------|
| `[tests/api/](tests/api/)` | ~150 | HTTP-тесты через FastAPI TestClient. Покрывают все эндпоинты: auth, sessions, coach, curator, gamification, analyst, rate limit, CORS, health, metrics |
| `[tests/unit/](tests/unit/)` | ~200 | Юнит-тесты: агенты (simulator, coach, curator), сервисы (auth, session, evaluation), fairness, entities, LLM providers, config validation |
| `[tests/integration/](tests/integration/)` | ~60 | Интеграционные тесты: DB, RAG, LiveKit, cross-component, observability, security |
| `[tests/e2e/](tests/e2e/)` | ~30 | Сквозные сценарии: auth flow, coach flow, full E2E features, performance, RBAC |
| `[tests/security/](tests/security/)` | ~5 | SAST base check |

**Покрытие:** ~84% (по данным последнего прогона).

**Ключевые тестовые файлы:**

| Файл | Тесты |
|------|-------|
| `[tests/api/test_sessions_api.py](tests/api/test_sessions_api.py)` | Session CRUD + step + finish |
| `[tests/api/test_auth_api.py](tests/api/test_auth_api.py)` | Register → Login → Refresh → Logout |
| `[tests/api/test_gamification_api.py](tests/api/test_gamification_api.py)` | XP, badges, leaderboard, streak |
| `[tests/api/test_fairness_api.py](tests/api/test_fairness_api.py)` | Fairness endpoints |
| `[tests/unit/test_coach_agent.py](tests/unit/test_coach_agent.py)` | 5-мерная оценка, фидбек «сэндвич» |
| `[tests/unit/test_simulator_agent.py](tests/unit/test_simulator_agent.py)` | Rule-based агент, 4 психотипа |
| `[tests/unit/test_fairness_metrics.py](tests/unit/test_fairness_metrics.py)` | Fairness metrics |
| `[tests/integration/test_cross_component.py](tests/integration/test_cross_component.py)` | Cross-component integration |
| `[tests/e2e/test_full_e2e_features.py](tests/e2e/test_full_e2e_features.py)` | Полный сценарий работы |

---

## 5. `docs-all/` — Документация (17 документов)

| # | Файл | Статус | Описание |
|---|------|--------|----------|
| 1 | `[README.md](./README.md)` | ✅ **Готово** | Точка входа: бейджи, C4 Container, стек, quick start |
| 2 | `[SPECIFICATION.md](./SPECIFICATION.md)` | ✅ **Готово** | Полная спецификация: FR, NFR, C4 L1-L3, ERD, API contracts, агенты |
| 3 | `[API.md](./API.md)` | ✅ **Готово** | REST API справочник: 34 эндпоинта, request/response, RBAC |
| 4 | `[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)` | ✅ **Готово** | ЭТОТ ФАЙЛ — навигация по репозиторию |
| 5 | `[SOURCE_CODE_REFERENCE.md](./SOURCE_CODE_REFERENCE.md)` | ✅ **Готово** | Навигатор по исходному коду |
| 6 | `[DATA_FLOWS.md](./DATA_FLOWS.md)` | ✅ **Готово** | Use cases + sequence-диаграммы |
| 7 | `[USER_GUIDE.md](./USER_GUIDE.md)` | 📋 Запланировано | Руководство пользователя |
| 8 | `[ADMIN_GUIDE.md](./ADMIN_GUIDE.md)` | 📋 Запланировано | Руководство администратора |
| 9 | `[DEPLOYMENT_PLAN.md](./DEPLOYMENT_PLAN.md)` | 📋 Запланировано | Production deployment |
| 10 | `[CICD.md](./CICD.md)` | 📋 Запланировано | CI/CD pipeline |
| 11 | `[TESTING.md](./TESTING.md)` | 📋 Запланировано | Стратегия тестирования |
| 12 | `[INTEGRATION_TEST_SPEC.md](./INTEGRATION_TEST_SPEC.md)` | 📋 Запланировано | Спецификация интеграционных тестов |
| 13 | `[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)` | 📋 Запланировано | Фазы имплементации |
| 14 | `[GLOSSARY.md](./GLOSSARY.md)` | 📋 Запланировано | Терминология |
| 15 | `[TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md)` | 📋 Запланировано | Устранение неполадок |
| 16 | `[adr/README.md](./adr/README.md)` | 📋 Запланировано | ADR index |
| 17 | `[adr/ARCHITECTURE_DECISIONS.md](./adr/ARCHITECTURE_DECISIONS.md)` | 📋 Запланировано | Architecture Decision Records |

---

## 6. Инфраструктура

### Docker

| Файл | Назначение |
|------|------------|
| `[docker-compose.dev.yml](docker-compose.dev.yml)` | Dev stack: app, PostgreSQL, Redis, Qdrant, MinIO |
| `[docker-compose.prod.yml](docker-compose.prod.yml)` | Production stack + Nginx, Prometheus, Grafana |
| `[Dockerfile.dev](Dockerfile.dev)` | Dev-сборка (hot reload) |
| `[Dockerfile.prod](Dockerfile.prod)` | Multi-stage prod-сборка |

### CI/CD (GitHub Actions)

| Файл | Pipeline |
|------|----------|
| `[.github/workflows/ci.yml](.github/workflows/ci.yml)` | Lint → Unit Tests → Integration Tests → Build |
| `[.github/workflows/security.yml](.github/workflows/security.yml)` | Security scan (SAST) |

### Конфигурация

| Файл | Назначение |
|------|------------|
| `[pyproject.toml](pyproject.toml)` | Python проект: зависимости, ruff, mypy, pytest |
| `alembic.ini` | DB migrations config |
| `[.env.example](.env.example)` | Пример переменных окружения |
| `[.pre-commit-config.yaml](.pre-commit-config.yaml)` | Pre-commit hooks (ruff, mypy) |
| `[Makefile](Makefile)` | Основные команды (test, lint, run, seed, demo) |

---

## 7. Соглашения об именовании

| Артефакт | Соглашение | Пример |
|----------|------------|--------|
| Python файлы | `snake_case` | `session_service.py` |
| Python классы | `PascalCase` | `class SessionService` |
| Python функции | `snake_case` | `def create_session()` |
| Python переменные | `snake_case` | `session_id` |
| FastAPI роутеры | `router = APIRouter(prefix=...)` | `router.py` |
| TypeScript файлы | `camelCase.ts` / `PascalCase.tsx` | `authStore.ts`, `login.tsx` |
| TypeScript компоненты | `PascalCase` | `function LoginPage()` |
| Таблицы БД | `snake_case` (мн.ч.) | `users`, `sessions`, `xp_entries` |
| Колонки БД | `snake_case` | `created_at`, `session_id` |
| Сущности | `PascalCase` (ед.ч.) | `class User`, `class Session` |
| Имена директорий | `snake_case` (Python) / `camelCase` (TS) | `[src/core/entities/](src/core/entities/)` |

### Архитектурные принципы

- **DDD** (Domain-Driven Design): entities → services → interfaces → infrastructure
- **Feature-Sliced Design** (frontend): app → pages → features → entities → shared
- **DI** (Dependency Injection): все зависимости через параметры конструктора
- **In-memory first**: приложение работает без внешних сервисов (PostgreSQL, Redis, Qdrant)
- **Repository pattern**: единый интерфейс, две реализации (in-memory / PostgreSQL)

---

## Источники

- [src/](../src/) — Backend исходный код
- [frontend/src/](../frontend/src/) — Frontend исходный код
- [tests/](../tests/) — Test suite
- []() — Вся документация
- [docker-compose.dev.yml](../docker-compose.dev.yml) — Dev compose
- [Makefile](../Makefile) — Команды сборки/тестов
- [pyproject.toml](../pyproject.toml) — Конфигурация проекта
