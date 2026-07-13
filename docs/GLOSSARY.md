# Глоссарий — AI Roleplay Coach Hub

> Единый справочник терминов и сокращений для всех участников проекта.
> Документ состоит из трёх частей: **Быстрый справочник** (таблицы), **Подробный словарь** (описания с примерами кода и ссылками) и **Тематический указатель**.

---

# Часть I. Быстрый справочник

## 1. Сокращения

| Термин | Значение | Контекст |
|--------|----------|----------|
| **AI** | Artificial Intelligence | Все агенты (Simulator, Coach, Curator, Analyst) |
| **API** | Application Programming Interface | REST API поверх HTTP (FastAPI) |
| **ASR** | Automatic Speech Recognition | Планируется: интеграция Whisper |
| **CI/CD** | Continuous Integration / Continuous Deployment | GitHub Actions pipeline |
| **CORS** | Cross-Origin Resource Sharing | Middleware, разрешающий фронтенду вызывать бэкенд |
| **CPU** | Central Processing Unit | Ресурс сервера |
| **CRUD** | Create, Read, Update, Delete | Стандартные операции API |
| **DDA** | Dynamic Difficulty Adjustment | SimulatorAgent адаптирует сложность клиента |
| **DDD** | Domain-Driven Design | Архитектура бэкенда (entities, services, repositories) |
| **DI** | Dependency Injection | Связывание компонентов в `dependencies.py` |
| **DNS** | Domain Name System | Сетевые имена |
| **ERD** | Entity-Relationship Diagram | Модель данных (в SPECIFICATION.md) |
| **E2E** | End-to-End (testing) | Сквозные тесты полного пайплайна |
| **FR** | Functional Requirement | Функциональное требование (FR-1 — FR-7) |
| **FSD** | Feature-Sliced Design | Архитектура фронтенда |
| **FTE** | Full-Time Equivalent | Бизнес-метрика стоимости ручного коучинга |
| **GPU** | Graphics Processing Unit | Для LLM inference |
| **HTTP** | Hypertext Transfer Protocol | Протокол REST API |
| **HTTPS** | HTTP Secure | TLS-шифрованный HTTP |
| **JSON** | JavaScript Object Notation | Формат запросов/ответов API |
| **JWT** | JSON Web Token | Токены аутентификации (access + refresh) |
| **LLM** | Large Language Model | AI-модель для симуляции и коучинга |
| **LMS** | Learning Management System | Планируется: интеграция с внешними LMS |
| **MVP** | Minimum Viable Product | Текущий объём версии |
| **NFR** | Non-Functional Requirement | Нетребование (NFR-1 — NFR-7) |
| **P0/P1** | Priority 0 / Priority 1 | P0 = критический, P1 = важный |
| **RAG** | Retrieval-Augmented Generation | Qdrant векторный поиск для контекста |
| **RBAC** | Role-Based Access Control | Роли: operator / trainer / admin |
| **REST** | Representational State Transfer | Архитектурный стиль API |
| **ROI** | Return On Investment | Бизнес-метрика окупаемости |
| **S3** | Simple Storage Service | MinIO-совместимое объектное хранилище |
| **SAST** | Static Application Security Testing | Сканирование безопасности в CI |
| **SQL** | Structured Query Language | Запросы к базе данных |
| **TLS** | Transport Layer Security | Протокол шифрования |
| **TTS** | Text-to-Speech | Планируется: голосовой вывод |
| **UC** | Use Case | Сценарии использования в диаграммах |
| **UI** | User Interface | Страницы фронтенда |
| **UX** | User Experience | Качество взаимодействия |
| **VM** | Virtual Machine | Серверное развёртывание |
| **WSS** | WebSocket Secure | Реальное время (планируется) |
| **XP** | Experience Points | Игровая валюта геймификации |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)

---

## 2. AI-агенты

| Термин | Назначение | Файл | Связанные понятия |
|--------|-----------|------|-------------------|
| **SimulatorAgent** | Rule-based AI-клиент с DDA | `[src/agents/simulator/agent.py](src/agents/simulator/agent.py)` | DDA, Anti-Gaming |
| **SimulatorLLMAgent** | LLM-версия AI-клиента | `[src/agents/simulator_llm/agent.py](src/agents/simulator_llm/agent.py)` | LLM, mock/ollama/openai |
| **CoachAgent** | Оценка диалога по 6 измерениям | `[src/agents/coach/agent.py](src/agents/coach/agent.py)` | Sandwich feedback, linguistic markers |
| **CuratorAgent** | Генератор сценариев и квизов | `[src/agents/curator/agent.py](src/agents/curator/agent.py)` | Training plans, LMS sync |
| **Analyst** | Статистика + аудит справедливости | `[src/agents/analyst/fairness_service.py](src/agents/analyst/fairness_service.py)` | 4 метрики справедливости |
| **GamificationEngine** | XP, бейджи, лидерборд, streak | `[src/agents/gamification/engine.py](src/agents/gamification/engine.py)` | XP, Level, Badge, Streak |
| **LLMProviderFactory** | Выбор провайдера (mock/ollama/openai) | `[src/infrastructure/llm/factory.py](src/infrastructure/llm/factory.py)` | LLM_PROVIDER env var |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)

---

## 3. Архитектурные термины

| Термин | Значение | Контекст |
|--------|----------|---------|
| **ADR** | Architecture Decision Record | `[adr/](./adr/)` (17 записей) |
| **C4 Model** | Context, Container, Component, Code | 4-уровневые диаграммы архитектуры |
| **DDD** | Domain-Driven Design | Entities, Value Objects, Services, Repositories |
| **Repository Pattern** | Абстракция доступа к данным | `[src/core/interfaces/repositories.py](src/core/interfaces/repositories.py)` |
| **In-Memory Repository** | Хранилище без персистентности | `[src/infrastructure/memory/repositories.py](src/infrastructure/memory/repositories.py)` |
| **Circuit Breaker** | Изоляция отказов | `[src/core/services/circuit_breaker.py](src/core/services/circuit_breaker.py)` |
| **DI Container** | Внедрение зависимостей | `[src/api/dependencies.py](src/api/dependencies.py)` |
| **Async/Await** | Асинхронное программирование | Все I/O операции (asyncpg, httpx) |
| **Sandwich Feedback** | Начало → Улучшение → Конец | Формат оценки Coach |
| **Mock Mode** | Ноль внешних зависимостей | LLM_PROVIDER=mock, DB_MODE=memory |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)

---

## 4. Бизнес-термины

| Термин | Значение | Контекст |
|--------|----------|---------|
| **Operator** | Конечный пользователь, практикующий общение | Роль: operator |
| **Trainer** | Супервайзер, управляющий обучением группы | Роль: trainer |
| **Admin** | Системный администратор | Роль: admin |
| **Scenario** | Определение роли AI-клиента | Психотип + сложность + контекст |
| **Psychotype** | Тип личности клиента | aggressive, confused, demanding |
| **Session** | Один диалог с AI-клиентом | Содержит turns, status, evaluation |
| **Turn** | Один обмен (оператор + клиент) | JSON-запись в транскрипте |
| **Transcript** | Полная история диалога | Список turn |
| **Evaluation** | Анализ сессии Coach | 6 scores + feedback |
| **Streak** | Дни подряд с активностью | Отслеживается GamificationEngine |
| **Training Plan** | Упорядоченный набор сценариев | Назначается trainer |
| **Quiz** | Вопросы для проверки знаний | Генерируется CuratorAgent |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)

---

## 5. Термины геймификации

| Термин | Значение | Формула / Правила |
|--------|----------|-------------------|
| **XP** | Experience Points | 100 base per session + bonuses |
| **Level** | Уровень прогресса | `level = XP // 1000 + 1` |
| **Badge** | Достижение | 8 бейджей с критериями разблокировки |
| **Leaderboard** | Таблица рейтинга | Top 10 пользователей |
| **Streak** | Дни подряд | +200 XP бонус при >= 3 дней |
| **DDA** | Dynamic Difficulty Adjustment | 4 уровня (0-3) на основе успеха |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)

---

## 6. Инфраструктурные термины

| Термин | Назначение | Образ / Конфиг |
|--------|-----------|----------------|
| **PostgreSQL** | Основная БД | postgres:16-alpine |
| **Redis** | Кеш + rate limiting | redis:7-alpine |
| **Qdrant** | Векторная БД | qdrant/qdrant:v1.13.6 |
| **MinIO** | S3-хранилище (dev) | minio/minio |
| **Prometheus** | Сбор метрик | `[src/monitoring/](src/monitoring/)` |
| **Grafana** | Дашборды (план) | `[deploy/grafana/](deploy/grafana/)` |
| **Docker Compose** | Оркестрация контейнеров | `[docker-compose.dev.yml](docker-compose.dev.yml)` / `.prod.yml` |
| **Nginx** | Реверс-прокси (план) | `[deploy/nginx/](deploy/nginx/)` |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)

---

## 7. Термины фронтенда

| Термин | Назначение | Файл |
|--------|-----------|------|
| **React** | UI библиотека | `[frontend/src/](frontend/src/)` |
| **Vite** | Сборщик | `[frontend/vite.config.ts](frontend/vite.config.ts)` |
| **TypeScript** | Типизированный JavaScript | Весь фронтенд |
| **Tailwind CSS** | CSS-фреймворк | `[frontend/tailwind.config.js](frontend/tailwind.config.js)` |
| **Zustand** | Управление состоянием | `[frontend/src/stores/](frontend/src/stores/)` |
| **React Router** | Клиентская маршрутизация | `[frontend/src/App.tsx](frontend/src/App.tsx)` |
| **FSD** | Feature-Sliced Design | `[frontend/src/app/pages/widgets/features/shared/](frontend/src/app/pages/widgets/features/shared/)` |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)

---

# Часть II. Подробный словарь терминов


## 8.1. Core AI & LLM


### AI (Artificial Intelligence)

| | |
|---|---|
| **Определение** | Совокупность алгоритмов и моделей, которые симулируют интеллектуальное поведение AI-клиентов и обеспечивают коучинг операторов. В проекте AI представлен шестью агентами с различными задачами. |
| **Где используется** | Все AGENTS: SimulatorAgent, SimulatorLLMAgent, CoachAgent, CuratorAgent, Analyst, GamificationEngine |
| **Принцип работы** | Rule-based по умолчанию, LLM — улучшение. Каждый агент может работать с любым провайдером через `LLMProviderFactory`. |
| **Код** | `[src/agents/](src/agents/)` |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#ai-agents), [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md#adr-002) |
| **Связанные понятия** | LLM, Rule-Based, Agent, Provider Factory |

---

### LLM (Large Language Model)

| | |
|---|---|
| **Определение** | Большая языковая модель — нейросеть, способная генерировать человекоподобный текст. В проекте LLM используется как улучшение для AI-агентов, но не является обязательной. |
| **Зачем в проекте** | LLM даёт более естественные ответы AI-клиента и более качественную обратную связь Coach. В production режиме рекомендуется OpenAI (GPT-4o-mini). |
| **Провайдеры** | Три провайдера: **mock** (детерминированный, для тестов), **ollama** (локальный, open-source), **openai** (внешний API). Переключение через `LLM_PROVIDER` env var. |
| **Circuit Breaker** | При недоступности провайдера автоматическое переключение на следующий по цепочке (openai → ollama → mock). |
| **Код** | `[src/infrastructure/llm/provider_factory.py](src/infrastructure/llm/provider_factory.py)`, `[src/infrastructure/llm/providers/](src/infrastructure/llm/providers/)` |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#nfrd), [ADMIN_GUIDE.md](./ADMIN_GUIDE.md#llm) |
| **Связанные понятия** | LLMProviderFactory, Circuit Breaker, Mock Mode |

---

### DDA (Dynamic Difficulty Adjustment)

| | |
|---|---|
| **Определение** | Механизм адаптации сложности AI-клиента в реальном времени на основе успеха оператора в предыдущих сессиях. |
| **Уровни сложности** | 0 (легкий) — 3 (сложный). Уровень повышается после серии успешных сессий (>= 3 побед) и понижается после 3 поражений подряд. |
| **Как влияет на поведение** | На лёгком уровне AI-клиент задаёт наводящие вопросы и даёт подсказки. На сложном — использует профессиональную лексику, перебивает, создаёт стрессовые сценарии. |
| **Код** | `[src/services/dda/](src/services/dda/)` |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#fr-6), [DATA_FLOWS.md](./DATA_FLOWS.md#dda) |
| **Связанные понятия** | SimulatorAgent, Psychotype, Session |

---

### RAG (Retrieval-Augmented Generation)

| | |
|---|---|
| **Определение** | Техника дополнения генерации текста поиском релевантного контекста в векторной базе данных. |
| **Зачем в проекте** | CuratorAgent использует RAG для поиска подходящих сценариев по запросу trainer. Векторные эмбеддинги хранятся в Qdrant. |
| **Компоненты** | Qdrant (векторная БД) + эмбеддинг-модель (all-MiniLM-L6-v2) + CuratorAgent |
| **Код** | `[src/infrastructure/vector/](src/infrastructure/vector/)`, `[src/agents/curator/](src/agents/curator/)` |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#fr-4) |
| **Связанные понятия** | Qdrant, CuratorAgent, Embedding |

---

### Sandwich Feedback

| | |
|---|---|
| **Определение** | Формат обратной связи Coach по принципу «бутерброда»: сначала похвала, затем область для улучшения, затем ободряющее завершение. |
| **Структура** | 1. **Start** — что получилось хорошо ("Вы уверенно начали диалог...") 2. **Improve** — что можно улучшить ("Попробуйте использовать открытые вопросы...") 3. **End** — общая положительная оценка ("В целом диалог продуктивный, продолжайте в том же духе") |
| **Код** | `[src/agents/coach/prompts/](src/agents/coach/prompts/)` |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#fr-3) |
| **Связанные понятия** | CoachAgent, Evaluation, Linguistic Markers |

---

### Mock Mode

| | |
|---|---|
| **Определение** | Режим работы приложения без внешних зависимостей — все AI-ответы генерируются детерминированными правилами, данные хранятся в памяти. |
| **Как включить** | `LLM_PROVIDER=mock` и `DB_MODE=memory` или `docker compose --profile mock up` |
| **Зачем нужен** | Для разработки без Docker, для CI/CD тестов, для демонстраций без интернета. |
| **Ограничения** | Ответы AI менее естественны, данные не сохраняются после перезапуска. |
| **Код** | `[src/infrastructure/memory/repositories.py](src/infrastructure/memory/repositories.py)`, `[src/infrastructure/llm/providers/mock_provider.py](src/infrastructure/llm/providers/mock_provider.py)` |
| **Документация** | [ADMIN_GUIDE.md](./ADMIN_GUIDE.md#setup), [DEPLOYMENT_PLAN.md](./DEPLOYMENT_PLAN.md#mock) |
| **Связанные понятия** | In-Memory Repository, LLMProviderFactory, CI/CD |

---

### LLMProviderFactory

| | |
|---|---|
| **Определение** | Фабрика, которая создаёт нужного LLM-провайдера на основе переменной окружения `LLM_PROVIDER`. |
| **Принцип работы** | `LLMProviderFactory.create(provider_type: str) -> BaseLLMProvider`. Поддерживаемые типы: `mock`, `ollama`, `openai`. Если провайдер не указан — используется `mock`. |
| **Chain of Responsibility** | При недоступности провайдера фабрика пробует следующий по цепочке (openai → ollama → mock). |
| **Код** | `[src/infrastructure/llm/factory.py](src/infrastructure/llm/factory.py)` |
| **Тесты** | `[tests/unit/infrastructure/llm/test_factory.py](tests/unit/infrastructure/llm/test_factory.py)` |
| **Связанные понятия** | LLM, Provider, Circuit Breaker |

---

### SimulatorAgent (детально)

| | |
|---|---|
| **Определение** | Rule-based AI-агент, симулирующий клиента. Использует психотип, сложность (DDA) и контекст для генерации ответов по правилам. |
| **Поведение по психотипу** | **aggressive** — перебивает, повышает голос, использует восклицания. **confused** — переспрашивает, говорит неуверенно. **demanding** — требует результатов, указывает на сроки. **professional** — использует термины, деловой тон. **novice** — задаёт базовые вопросы. |
| **DDA-адаптация** | На уровне 0 (лёгкий) — отвечает медленно, даёт подсказки. На уровне 3 (сложный) — быстрые ответы, сложная лексика, стресс-сценарии. |
| **Форматы ответов** | Ответы генерируются по шаблонам, специфичным для каждого психотипа. Шаблоны содержат варианты реплик с разной эмоциональной окраской. |
| **Код** | `[src/agents/simulator/agent.py](src/agents/simulator/agent.py)`, `[src/agents/simulator/prompts/](src/agents/simulator/prompts/)` |
| **Тесты** | `[tests/unit/agents/simulator/](tests/unit/agents/simulator/)` |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#fr-2) |
| **Связанные понятия** | DDA, Psychotype, Scenario, Anti-Gaming |

---

### SimulatorLLMAgent

| | |
|---|---|
| **Определение** | LLM-версия SimulatorAgent. Использует LLM для генерации более естественных и разнообразных ответов. |
| **Параметры** | Тот же психотип, контекст, уровень DDA. LLM получает их в system prompt. |
| **Когда используется** | При LLM_PROVIDER=openai или ollama. Недоступен в mock-режиме. |
| **Код** | `[src/agents/simulator_llm/agent.py](src/agents/simulator_llm/agent.py)` |
| **Связанные понятия** | SimulatorAgent, LLM, DDA |

---

### CoachAgent (детально)

| | |
|---|---|
| **Определение** | AI-агент, оценивающий диалог оператора по 6 измерениям и дающий Sandwich Feedback. |
| **Процесс оценки** | 1. Получает полный транскрипт сессии 2. Анализирует каждое измерение по лингвистическим маркерам 3. Вычисляет баллы (0-100) 4. Формирует Sandwich Feedback |
| **Rule-based режим** | Использует предопределённые правила: количество вопросов, время ответа, ключевые слова эмпатии и т.д. |
| **LLM-режим** | LLM анализирует транскрипт в контексте, даёт более глубокую оценку с учётом нюансов диалога. |
| **Лингвистические маркеры** | Подсчёт открытых/закрытых вопросов, слов эмпатии («понимаю», «сочувствую»), маркеров активного слушания («то есть вы говорите...»). |
| **Код** | `[src/agents/coach/agent.py](src/agents/coach/agent.py)`, `[src/agents/coach/scoring/](src/agents/coach/scoring/)` |
| **Тесты** | `[tests/unit/agents/coach/](tests/unit/agents/coach/)` |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#fr-3), [API.md](./API.md#evaluation) |
| **Связанные понятия** | Evaluation, Sandwich Feedback, Linguistic Markers |

---

### CuratorAgent (детально)

| | |
|---|---|
| **Определение** | AI-агент, генерирующий учебные сценарии, квизы и тренировочные планы. |
| **Генерация сценариев** | По запросу trainer создаёт сценарий: название, контекст, психотип, сложность, цели обучения. |
| **Генерация квизов** | После сессии может сгенерировать 3-5 вопросов для проверки понимания темы. |
| **Тренировочные планы** | На основе слабых мест оператора (анализ 6-dim оценок) составляет последовательность сценариев. |
| **Код** | `[src/agents/curator/agent.py](src/agents/curator/agent.py)` |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#fr-4) |
| **Связанные понятия** | Scenario, Quiz, Training Plan, RAG |

---

### Analyst (детально)

| | |
|---|---|
| **Определение** | AI-агент для статистического анализа и аудита справедливости модели. |
| **Метрики справедливости** | 1. **Demographic Parity** — равная доля положительных оценок для разных групп 2. **Equal Opportunity** — равная вероятность получить высокую оценку при равном качестве 3. **Predictive Parity** — одинаковое значение баллов для одинакового качества 4. **Individual Fairness** — похожие диалоги → похожие оценки |
| **Код** | `[src/agents/analyst/fairness_service.py](src/agents/analyst/fairness_service.py)` |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#fr-7) |
| **Связанные понятия** | CoachAgent, Evaluation, Fairness |

---

### Anti-Gaming

| | |
|---|---|
| **Определение** | Механизмы предотвращения эксплуатации системы геймификации (накрутка XP, бейджей, лидерборда). |
| **Механизмы** | 1. **Минимальная длина диалога** — сессия должна содержать не менее 3 turn 2. **Максимум сессий в день** — не более 20 (настраивается) 3. **Детектор повторяющихся ответов** — если оператор отправляет одинаковые сообщения, сессия не оценивается 4. **Анти-спам лидерборда** — топ-10 обновляется не чаще раза в час |
| **Код** | `[src/agents/gamification/anti_gaming.py](src/agents/gamification/anti_gaming.py)` |
| **Связанные понятия** | GamificationEngine, XP, Badge, Streak |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)


## 8.2. Архитектура


### ADR (Architecture Decision Record)

| | |
|---|---|
| **Определение** | Документ, фиксирующий важное архитектурное решение, его контекст, альтернативы и обоснование. |
| **Где хранятся** | `[adr/](./adr/)` — 17 записей (Round 17). |
| **Структура ADR** | 1. Title и статус 2. Context — почему решение нужно 3. Decision — что решили 4. Consequences — последствия и компромиссы |
| **Примеры** | ADR-001: In-Memory First, ADR-002: Multiple Agents, ADR-003: 6-Dimension Scoring |
| **Документация** | [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md#adr) |
| **Связанные понятия** | Architecture Decision, ADR, Round |

---

### Repository Pattern

| | |
|---|---|
| **Определение** | Паттерн, абстрагирующий доступ к данным за интерфейсом репозитория. Бизнес-логика не знает, в какой БД хранятся данные. |
| **Интерфейсы** | `ISessionRepository`, `IUserRepository`, `IScenarioRepository`, `IEvaluationRepository`, `IQuizRepository` — в `[src/core/interfaces/repositories.py](src/core/interfaces/repositories.py)` |
| **Реализации** | **Memory** — `[src/infrastructure/memory/repositories.py](src/infrastructure/memory/repositories.py)` (In-Memory, для dev/test/mock). **PostgreSQL** — `[src/infrastructure/postgres/repositories.py](src/infrastructure/postgres/repositories.py)` (asyncpg, для production). |
| **Фабрика** | `RepositoryFactory.create(db_mode)` — выбирает реализацию на основе `DB_MODE` (memory / postgres). |
| **Код** | `[src/core/interfaces/repositories.py](src/core/interfaces/repositories.py)`, `[src/infrastructure/repository_factory.py](src/infrastructure/repository_factory.py)` |
| **Тесты** | `[tests/unit/infrastructure/repositories/](tests/unit/infrastructure/repositories/)` |
| **Связанные понятия** | In-Memory Repository, DDD, DI |

---

### In-Memory Repository

| | |
|---|---|
| **Определение** | Реализация Repository Pattern, хранящая данные в памяти процесса (в `dict` и `list`). |
| **Особенности** | 1. Данные не сохраняются между перезапусками 2. Максимальная скорость (нет I/O) 3. Не требует Docker/PostgreSQL 4. Идеально для тестов и разработки |
| **Когда используется** | 1. Локальная разработка без Docker 2. CI/CD (GitHub Actions) 3. Модульные тесты 4. Демонстрации без интернета |
| **Код** | `[src/infrastructure/memory/repositories.py](src/infrastructure/memory/repositories.py)` |
| **Тесты** | Те же интерфейсы, что и PostgreSQL-реализация — идентичное поведение |
| **Связанные понятия** | Repository Pattern, Mock Mode |

---

### Circuit Breaker

| | |
|---|---|
| **Определение** | Паттерн отказоустойчивости, предотвращающий повторные вызовы к отказавшему внешнему сервису. |
| **Состояния** | **Closed** — вызовы проходят, ошибки считаются. **Open** — вызовы блокируются (таймаут). **Half-Open** — пробный вызов для проверки восстановления. |
| **Параметры** | `failure_threshold=5` (ошибок до Open), `recovery_timeout=30` (секунд до Half-Open), `half_open_max_retries=3`. |
| **Код** | `[src/core/services/circuit_breaker.py](src/core/services/circuit_breaker.py)` |
| **Тесты** | `[tests/unit/core/services/test_circuit_breaker.py](tests/unit/core/services/test_circuit_breaker.py)` |
| **Связанные понятия** | LLMProviderFactory, Fail Gracefully |

---

### DI Container (Dependency Injection Container)

| | |
|---|---|
| **Определение** | Механизм связывания зависимостей приложения — репозиториев, сервисов, фабрик. |
| **Реализация** | FastAPI Depends — `[src/api/dependencies.py](src/api/dependencies.py)` |
| **Пример** | `SessionService(session_repo=Depends(get_session_repo), coach_agent=Depends(get_coach_agent))` |
| **Код** | `[src/api/dependencies.py](src/api/dependencies.py)` |
| **Связанные понятия** | Repository Pattern, FastAPI, Dependency Injection |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)


## 8.3. Инфраструктура и развёртывание


### PostgreSQL

| | |
|---|---|
| **Определение** | Реляционная база данных, используемая в production-режиме для хранения всех данных приложения. |
| **Версия** | 16 Alpine (образ Docker) |
| **Расширения** | `pg_stat_statements` (мониторинг производительности) |
| **Схема** | Миграции в `[src/infrastructure/postgres/migrations/](src/infrastructure/postgres/migrations/)` |
| **Абстракция** | Доступ через Repository Pattern — бизнес-логика не содержит SQL-запросов |
| **Когда используется** | Production-режим (`DB_MODE=postgres`). Для разработки — In-Memory репозитории. |
| **Код** | `[src/infrastructure/postgres/](src/infrastructure/postgres/)` |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#infrastructure), [DEPLOYMENT_PLAN.md](./DEPLOYMENT_PLAN.md#postgres) |
| **Связанные понятия** | Repository Pattern, SQL, Migration |

---

### Redis

| | |
|---|---|
| **Определение** | In-memory data store, используемый для кеширования и rate limiting. |
| **Назначение** | 1. **Кеш** — хранение часто запрашиваемых данных (сценарии, рейтинги) 2. **Rate Limiting** — Token Bucket для API 3. **Pub/Sub** — уведомления о событиях (планируется) |
| **Версия** | 7 Alpine |
| **Абстракция** | `ICacheService` — интерфейс с реализациями Redis и In-Memory |
| **Код** | `[src/infrastructure/cache/](src/infrastructure/cache/)` |
| **Связанные понятия** | Cache, Rate Limiting |

---

### Qdrant

| | |
|---|---|
| **Определение** | Векторная база данных для RAG-поиска сценариев и контекстов. |
| **Версия** | v1.13.6 |
| **Размерность** | 384 (all-MiniLM-L6-v2) |
| **Когда используется** | CuratorAgent использует Qdrant для поиска релевантных сценариев по текстовому запросу trainer. |
| **Абстракция** | `IVectorRepository` — интерфейс с реализациями Qdrant и In-Memory (для тестов) |
| **Код** | `[src/infrastructure/vector/](src/infrastructure/vector/)` |
| **Связанные понятия** | RAG, CuratorAgent, Embedding |

---

### Docker Compose

| | |
|---|---|
| **Определение** | Инструмент оркестрации многоконтейнерных Docker-приложений. |
| **Профили** | `dev` — полный набор для разработки, `mock` — без внешних зависимостей, `monitoring` — Prometheus + Grafana |
| **Файлы** | `[docker-compose.dev.yml](docker-compose.dev.yml)` (разработка), `[docker-compose.prod.yml](docker-compose.prod.yml)` (production), `.env` (конфигурация) |
| **Сервисы** | Backend (FastAPI), Frontend (Vite), PostgreSQL, Redis, Qdrant, MinIO, Prometheus |
| **Документация** | [DEPLOYMENT_PLAN.md](./DEPLOYMENT_PLAN.md#docker) |
| **Связанные понятия** | Docker, Container, [Dockerfile](Dockerfile) |

---

### CI/CD (GitHub Actions)

| | |
|---|---|
| **Определение** | Автоматизация сборки, тестирования и развёртывания через GitHub Actions. |
| **Воркфлоу** | 1. **CI** — lint → typecheck → unit tests → integration tests → build 2. **CD** — deploy to staging → E2E tests → deploy to production |
| **Безопасность** | SAST-сканирование (Semgrep) + secrets scan + dependency audit в каждом PR |
| **Конфиг** | `[.github/workflows/](.github/workflows/)` |
| **Документация** | [CICD.md](./CICD.md) |
| **Связанные понятия** | SAST, E2E, Pipeline |

---

### Prometheus + Grafana

| | |
|---|---|
| **Определение** | Стек мониторинга: Prometheus собирает метрики, Grafana их визуализирует. |
| **Метрики** | Request latency (p50/p95/p99), request rate, error rate, LLM latency, LLM error rate, queue depth, active sessions |
| **Экспорт метрик** | FastAPI Prometheus middleware (`[src/monitoring/metrics.py](src/monitoring/metrics.py)`) |
| **Дашборды** | Grafana в `[deploy/grafana/dashboards/](deploy/grafana/dashboards/)` (планируется) |
| **Алерты** | Prometheus AlertManager (планируется) |
| **Код** | `[src/monitoring/](src/monitoring/)` |
| **Документация** | [ADMIN_GUIDE.md](./ADMIN_GUIDE.md#monitoring) |
| **Связанные понятия** | Metrics, Alerting, SLO |

---

### [Dockerfile](Dockerfile)

| | |
|---|---|
| **Определение** | Инструкция для сборки Docker-образа бэкенда. |
| **Особенности** | Многоступенчатая сборка (multi-stage): слой зависимостей (poetry.lock) → код → финальный образ. Использует `slim` образ для минимизации размера. |
| **Размер образа** | ~150 MB (production), ~400 MB (dev с инструментами) |
| **Файл** | `[Dockerfile](Dockerfile)` (backend), `[frontend/Dockerfile](frontend/Dockerfile)` (frontend) |
| **Связанные понятия** | Docker Compose, Docker Image |

---

### nginx

| | |
|---|---|
| **Определение** | Веб-сервер и reverse proxy. Планируется для production-развёртывания. |
| **Функции** | 1. Reverse proxy для backend API 2. Статическая раздача фронтенда 3. TLS termination 4. Rate limiting |
| **Конфиг** | `[deploy/nginx/default.conf](deploy/nginx/default.conf)` (планируется) |
| **Связанные понятия** | TLS, Reverse Proxy, Docker Compose |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)


## 8.4. Безопасность


### RBAC (Role-Based Access Control)

| | |
|---|---|
| **Определение** | Система управления доступом на основе ролей. |
| **Роли** | **operator** — практикует диалоги, просматривает свою статистику. **trainer** — управляет группой, назначает сценарии, смотрит аналитику группы. **admin** — управляет пользователями, системными настройками, мониторингом. |
| **Матрица доступа** | operator: только свои сессии → trainer: сессии группы → admin: всё |
| **Код** | `[src/api/auth.py](src/api/auth.py)`, `[src/core/entities/user.py](src/core/entities/user.py)` |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#nfrd) |
| **Связанные понятия** | Auth, JWT |

---

### JWT (JSON Web Token)

| | |
|---|---|
| **Определение** | Токен аутентификации в формате JSON, подписанный секретным ключом. |
| **Типы** | **Access token** — короткоживущий (15 минут), для доступа к API. **Refresh token** — долгоживущий (7 дней), для обновления access token. |
| **Где используется** | Все API-запросы (кроме /auth и /health) требуют заголовка `Authorization: Bearer <access_token>`. |
| **Хранение** | Access token — в памяти (Zustand store). Refresh token — в httpOnly cookie. |
| **Код** | `[src/api/auth.py](src/api/auth.py)` |
| **Связанные понятия** | RBAC, Auth, Cookie |

---

### SAST (Static Application Security Testing)

| | |
|---|---|
| **Определение** | Статический анализ исходного кода на уязвимости. |
| **Инструмент** | Semgrep с правилами OWASP Top 10 |
| **Когда запускается** | При каждом push/PR в CI/CD пайплайне |
| **Порог** | Medium и выше — блокировка PR |
| **Документация** | [CICD.md](./CICD.md#security) |
| **Связанные понятия** | CI/CD, Security Scan |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)


## 8.5. Бизнес-домен


### Operator

| | |
|---|---|
| **Определение** | Конечный пользователь приложения, практикующий коммуникативные навыки через диалог с AI-клиентами. |
| **Действия** | 1. Выбирает или получает сценарий 2. Ведёт диалог с AI-клиентом 3. Получает оценку Coach 4. Отслеживает свой прогресс (XP, уровень, бейджи) |
| **Мотивация** | Геймификация (бейджи, XP, лидерборд) + учебные цели (улучшение навыков) |
| **Код** | `[src/core/entities/user.py](src/core/entities/user.py)` (role=operator) |
| **Документация** | [USER_GUIDE.md](./USER_GUIDE.md#operator) |
| **Связанные понятия** | Trainer, Session, Scenario, XP |

---

### Scenario (Сценарий)

| | |
|---|---|
| **Определение** | Роль AI-клиента, включающая психотип, уровень сложности и контекст диалога. |
| **Компоненты** | **Название**, **Описание контекста**, **Психотип**, **Уровень сложности** (0-3), **Цель обучения**, **Ключевые навыки** |
| **Психотипы** | aggressive (агрессивный клиент), confused (растерянный), demanding (требовательный), professional (профессионал), novice (новичок) |
| **Хранилище** | PostgreSQL + Qdrant (для векторного поиска) |
| **Код** | `[src/core/entities/scenario.py](src/core/entities/scenario.py)`, `[src/services/scenario_service.py](src/services/scenario_service.py)` |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#fr-1), [USER_GUIDE.md](./USER_GUIDE.md#scenarios) |
| **Связанные понятия** | Psychotype, DDA, Training Plan |

---

### Session (Сессия)

| | |
|---|---|
| **Определение** | Один полный диалог оператора с AI-клиентом. |
| **Жизненный цикл** | `pending` → `active` (идет диалог) → `completed` (диалог завершён) → `evaluated` (Coach оценил) |
| **Содержимое** | scenario_id, user_id, список turn (диалог), evaluation (после завершения), статус, временные метки |
| **Максимум** | 50 turn на сессию |
| **Код** | `[src/core/entities/session.py](src/core/entities/session.py)`, `[src/services/session_service.py](src/services/session_service.py)` |
| **API** | POST /sessions, GET /sessions/{id}, POST /sessions/{id}/evaluate |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#fr-2), [API.md](./API.md#sessions) |
| **Связанные понятия** | Turn, Transcript, Evaluation |

---

### Evaluation (Оценка)

| | |
|---|---|
| **Определение** | Анализ сессии CoachAgent по 6 измерениям. |
| **Измерения** | 1. **rapport** — установление контакта 2. **listening** — активное слушание 3. **questioning** — качество вопросов 4. **empathy** — эмпатия 5. **clarity** — ясность выражения 6. **structure** — структура диалога |
| **Формат** | Каждое измерение: 0-100 баллов + текстовый фидбек. Общий фидбек — Sandwich Feedback. |
| **Код** | `[src/core/entities/evaluation.py](src/core/entities/evaluation.py)`, `[src/agents/coach/](src/agents/coach/)` |
| **API** | POST /sessions/{id}/evaluate |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#fr-3), [API.md](./API.md#evaluation) |
| **Связанные понятия** | CoachAgent, Sandwich Feedback, Session |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)


## 8.6. Геймификация (детально)


### XP (Experience Points)

| | |
|---|---|
| **Определение** | Основная игровая валюта. Начисляется за завершение сессий, получение высоких оценок, поддержание streak. |
| **Формула** | `XP = 100 (base) + score_bonus + streak_bonus` |
| **Score bonus** | Если средняя оценка > 75 → +50 XP. > 90 → +100 XP. |
| **Streak bonus** | >= 3 дней подряд → +200 XP. >= 7 дней → +500 XP. >= 30 дней → +1000 XP. |
| **Код** | `[src/agents/gamification/engine.py](src/agents/gamification/engine.py)` |
| **Связанные понятия** | Level, Badge, Streak |

---

### Level (Уровень)

| | |
|---|---|
| **Определение** | Показатель прогресса оператора. |
| **Формула** | `level = total_xp // 1000 + 1` |
| **Примеры** | 0 XP → Level 1, 1000 XP → Level 2, 5000 XP → Level 6 |
| **Бонусы** | Каждый новый уровень открывает доступ к более сложным сценариям. |
| **Код** | `[src/agents/gamification/engine.py](src/agents/gamification/engine.py)` |
| **Связанные понятия** | XP, DDA |

---

### Badge (Бейдж)

| | |
|---|---|
| **Определение** | Достижение, которое разблокируется при выполнении определённых условий. |
| **Список бейджей** | 1. **First Steps** — первая сессия 2. **Conversationalist** — 10 сессий 3. **Expert** — уровень 10 4. **Peacemaker** — успокоить агрессивного клиента 5. **Streak Master** — 7-дневный streak 6. **Quick Learner** — средняя оценка > 90 7. **Trainer** — провести 5 сессий с разными сценариями 8. **Veteran** — 100 сессий |
| **Код** | `[src/agents/gamification/badges.py](src/agents/gamification/badges.py)` |
| **Связанные понятия** | XP, Streak, Achievement |

---

### Streak (Серия)

| | |
|---|---|
| **Определение** | Количество дней подряд с хотя бы одной завершённой сессией. |
| **Правила** | Сбрасывается в 0, если пропущен день. Отсчёт от первого дня активности. Учитывается часовой пояс пользователя (UTC+0). |
| **Бонусы** | 3+ дней → +200 XP, 7+ → +500 XP, 30+ → +1000 XP |
| **Код** | `[src/agents/gamification/streak_service.py](src/agents/gamification/streak_service.py)` |
| **Связанные понятия** | XP, GamificationEngine |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)


## 8.7. Тестирование


### Unit Tests

| | |
|---|---|
| **Определение** | Модульные тесты, проверяющие один компонент изолированно. Все внешние зависимости заменены In-Memory репозиториями и mock-провайдерами. |
| **Фреймворк** | pytest |
| **Покрытие** | Core services, agents, infrastructure — > 460 тестов |
| **Как запускать** | `pytest tests/unit/` |
| **Код** | `[tests/unit/](tests/unit/)` |
| **Связанные понятия** | In-Memory Repository, Mock Mode, CI/CD |

---

### Integration Tests

| | |
|---|---|
| **Определение** | Тесты, проверяющие взаимодействие компонентов через реальный API. |
| **Фреймворк** | pytest + httpx (AsyncClient) |
| **Сценарии** | Создание сессии → добавление turn → оценка Coach → проверка результата |
| **Как запускать** | `pytest tests/integration/` |
| **Код** | `[tests/integration/](tests/integration/)` |
| **Документация** | [INTEGRATION_TEST_SPEC.md](./INTEGRATION_TEST_SPEC.md) |
| **Связанные понятия** | API, E2E, HTTP |

---

### E2E Tests

| | |
|---|---|
| **Определение** | Сквозные тесты, проверяющие полный пользовательский сценарий через API. |
| **Сценарии** | Login → Complete scenario → Evaluate → Check XP |
| **Как запускать** | `pytest tests/e2e/` |
| **Код** | `[tests/e2e/](tests/e2e/)` |
| **Связанные понятия** | Integration Tests, API |

---

### Fixtures

| | |
|---|---|
| **Определение** | Тестовые фикстуры pytest, создающие изолированное окружение для каждого теста. |
| **Основные фикстуры** | `in_memory_repositories` — чистые In-Memory репозитории для каждого теста. `mock_llm_provider` — детерминированный LLM-провайдер. `async_client` — HTTP-клиент для интеграционных тестов. `auth_headers` — JWT-токен для авторизованных запросов. |
| **Scope** | По умолчанию `function` — каждая тест-функция получает свежие репозитории. |
| **Код** | `[tests/conftest.py](tests/conftest.py)`, `[tests/unit/conftest.py](tests/unit/conftest.py)`, `[tests/integration/conftest.py](tests/integration/conftest.py)` |
| **Связанные понятия** | In-Memory Repository, pytest, Mock Mode |

---

## 8.8. Процессы и требования


### FR (Functional Requirement)

| | |
|---|---|
| **Определение** | Функциональное требование — конкретная функция, которую должно выполнять приложение. |
| **Список** | FR-1: Управление сценариями, FR-2: AI-клиент, FR-3: Оценка Coach, FR-4: Куратор, FR-5: Геймификация, FR-6: DDA, FR-7: Справедливость |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#функциональные-требования) |
| **Связанные понятия** | NFR, Specification |

---

### NFR (Non-Functional Requirement)

| | |
|---|---|
| **Определение** | Нефункциональное требование — качественная характеристика системы. |
| **Список** | NFR-A: Доступность (99.9%), NFR-B: Производительность (p95 < 500ms), NFR-C: Безопасность (RBAC, JWT), NFR-D: Отказоустойчивость (Circuit Breaker), NFR-E: Масштабируемость, NFR-F: Тестируемость, NFR-G: Модифицируемость |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#нефункциональные-требования) |
| **Связанные понятия** | FR, Specification, SLO |

---

### Use Case (UC)

| | |
|---|---|
| **Определение** | Сценарий использования — последовательность действий пользователя и системы для достижения конкретной цели. |
| **Список UC** | UC-1: Оператор проходит сценарий, UC-2: Тренер назначает план, UC-3: Администратор управляет системой |
| **Диаграммы** | Mermaid sequence diagrams в [DATA_FLOWS.md](./DATA_FLOWS.md) |
| **Документация** | [DATA_FLOWS.md](./DATA_FLOWS.md) |
| **Связанные понятия** | Scenario, Session, FR |

---

### ERD (Entity-Relationship Diagram)

| | |
|---|---|
| **Определение** | Диаграмма, описывающая сущности данных и связи между ними. |
| **Сущности** | User, Session, Scenario, Turn, Evaluation, Badge, TrainingPlan, Quiz |
| **Диаграмма** | Mermaid ERD в [SPECIFICATION.md](./SPECIFICATION.md#сущности-и-связи) |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#сущности-и-связи) |
| **Связанные понятия** | Repository Pattern, SQL, Entity |

---

### SLO (Service Level Objective)

| | |
|---|---|
| **Определение** | Целевой уровень качества сервиса. Измеряется через мониторинг. |
| **Текущие SLO** | p95 latency < 500ms (API), LLM response < 5s, Uptime > 99.9%, Error rate < 1% |
| **Метрики** | Prometheus собирает latency, error rate, request rate |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#nfrb) |
| **Связанные понятия** | Prometheus, NFR, Monitoring |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)


## 8.8. Фронтенд


### FSD (Feature-Sliced Design)

| | |
|---|---|
| **Определение** | Методология организации кода фронтенда, разделяющая приложение на слои по уровням абстракции. |
| **Слои** | **app** — инициализация, роутинг, глобальные стили. **pages** — страницы (LoginPage, DashboardPage, SessionPage). **widgets** — самостоятельные блоки (ScenarioCard, ScoreChart). **features** — бизнес-логика: создания сессии, оценка, фильтрация. **shared** — переиспользуемые компоненты, UI-kit, helpers. |
| **Почему FSD** | 1. Понятная навигация по проекту 2. Чёткие границы ответственности 3. Легко удалять/добавлять фичи |
| **Код** | `[frontend/src/](frontend/src/)` |
| **Связанные понятия** | React, Zustand, Feature |

---

### Zustand

| | |
|---|---|
| **Определение** | Лёгкая библиотека управления состоянием для React. |
| **Хранилища** | `useSessionStore` — текущая сессия и turn. `useAuthStore` — токен, пользователь. `useUIStore` — тема, sidebar. |
| **Почему не Redux** | Zustand требует в 5 раз меньше boilerplate (нет actions, reducers, sagas) и имеет тот же уровень предсказуемости. |
| **Код** | `[frontend/src/stores/](frontend/src/stores/)` |
| **Связанные понятия** | React, State Management |

---

### Tailwind CSS

| | |
|---|---|
| **Определение** | Utility-first CSS-фреймворк. Стили задаются через классы прямо в JSX. |
| **Почему Tailwind** | 1. Единая дизайн-система (спейсинг, цвета, типографика) 2. Нет конфликтов CSS-классов 3. Маленький итоговый CSS (purge) |
| **Темизация** | CSS Variables + Tailwind dark mode |
| **Код** | `[frontend/tailwind.config.js](frontend/tailwind.config.js)`, `[frontend/src/app/styles/](frontend/src/app/styles/)` |
| **Связанные понятия** | CSS, React, Theming |

[↑ К оглавлению](#глоссарий--ai-roleplay-coach-hub)


# Часть III. Тематический указатель

## AI & Агенты

| Понятие | Раздел | Документация |
|---------|--------|-------------|
| AI | [8.1](#ai-artificial-intelligence) | [SPEC → Agents](./SPECIFICATION.md#ai-agents) |
| LLM | [8.1](#llm-large-language-model) | [ADMIN → LLM](./ADMIN_GUIDE.md#llm) |
| SimulatorAgent | [2](#2-ai-агенты) | [SPEC → FR-2](./SPECIFICATION.md#fr-2) |
| CoachAgent | [2](#2-ai-агенты) | [SPEC → FR-3](./SPECIFICATION.md#fr-3) |
| CuratorAgent | [2](#2-ai-агенты) | [SPEC → FR-4](./SPECIFICATION.md#fr-4) |
| DDA | [8.1](#dda-dynamic-difficulty-adjustment) | [SPEC → FR-6](./SPECIFICATION.md#fr-6) |
| RAG | [8.1](#rag-retrieval-augmented-generation) | [SPEC → FR-5](./SPECIFICATION.md#fr-5) |
| Sandwich Feedback | [8.1](#sandwich-feedback) | [SPEC → FR-3](./SPECIFICATION.md#fr-3) |
| Mock Mode | [8.1](#mock-mode) | [ADMIN → Setup](./ADMIN_GUIDE.md#setup) |
| LLMProviderFactory | [8.1](#llmproviderfactory) | [ADMIN → LLM](./ADMIN_GUIDE.md#llm) |

## Архитектура

| Понятие | Раздел | Документация |
|---------|--------|-------------|
| ADR | [8.2](#adr-architecture-decision-record) | [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md) |
| Repository Pattern | [8.2](#repository-pattern) | [SPEC → Data Layer](./SPECIFICATION.md#data-layer) |
| In-Memory Repository | [8.2](#in-memory-repository) | [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md#adr-001) |
| Circuit Breaker | [8.2](#circuit-breaker) | [SPEC → NFR-D](./SPECIFICATION.md#nfrd) |
| DI Container | [8.2](#di-container-dependency-injection-container) | `[src/api/dependencies.py](src/api/dependencies.py)` |
| C4 Model | [3](#3-архитектурные-термины) | [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md) |
| FSD | [8.8](#fsd-feature-sliced-design) | `[frontend/src/](frontend/src/)` |

## Инфраструктура

| Понятие | Раздел | Документация |
|---------|--------|-------------|
| PostgreSQL | [8.3](#postgresql) | [DEPLOYMENT_PLAN.md](./DEPLOYMENT_PLAN.md#postgres) |
| Redis | [8.3](#redis) | `[src/infrastructure/cache/](src/infrastructure/cache/)` |
| Qdrant | [8.3](#qdrant) | `[src/infrastructure/vector/](src/infrastructure/vector/)` |
| Docker Compose | [8.3](#docker-compose) | [DEPLOYMENT_PLAN.md](./DEPLOYMENT_PLAN.md#docker) |
| CI/CD | [8.3](#cicd-github-actions) | [CICD.md](./CICD.md) |
| SAST | [8.4](#sast-static-application-security-testing) | [CICD.md](./CICD.md#security) |
| MinIO | [6](#6-инфраструктурные-термины) | [DEPLOYMENT_PLAN.md](./DEPLOYMENT_PLAN.md) |

## Безопасность

| Понятие | Раздел | Документация |
|---------|--------|-------------|
| RBAC | [8.4](#rbac-role-based-access-control) | [SPEC → NFR-C](./SPECIFICATION.md#nfrc) |
| JWT | [8.4](#jwt-json-web-token) | [API.md](./API.md#auth) |
| TLS | [1](#1-сокращения) | [DEPLOYMENT_PLAN.md](./DEPLOYMENT_PLAN.md#security) |
| CORS | [1](#1-сокращения) | `[src/api/main.py](src/api/main.py)` |

## Бизнес

| Понятие | Раздел | Документация |
|---------|--------|-------------|
| Operator | [8.5](#operator) | [USER_GUIDE.md](./USER_GUIDE.md#operator) |
| Trainer | [4](#4-бизнес-термины) | [USER_GUIDE.md](./USER_GUIDE.md#trainer) |
| Scenario | [8.5](#scenario-сценарий) | [SPEC → FR-1](./SPECIFICATION.md#fr-1) |
| Session | [8.5](#session-сессия) | [API.md](./API.md#sessions) |
| Evaluation | [8.5](#evaluation-оценка) | [SPEC → FR-3](./SPECIFICATION.md#fr-3) |
| Psychotype | [8.5](#scenario-сценарий) | `[src/core/entities/scenario.py](src/core/entities/scenario.py)` |
| Training Plan | [4](#4-бизнес-термины) | [SPEC → FR-4](./SPECIFICATION.md#fr-4) |
| Quiz | [4](#4-бизнес-термины) | [SPEC → FR-4](./SPECIFICATION.md#fr-4) |

## Геймификация

| Понятие | Раздел | Документация |
|---------|--------|-------------|
| XP | [8.6](#xp-experience-points) | [SPEC → FR-5](./SPECIFICATION.md#fr-5) |
| Level | [8.6](#level-уровень) | `[src/agents/gamification/engine.py](src/agents/gamification/engine.py)` |
| Badge | [8.6](#badge-бейдж) | `[src/agents/gamification/badges.py](src/agents/gamification/badges.py)` |
| Streak | [8.6](#streak-серия) | `[src/agents/gamification/streak_service.py](src/agents/gamification/streak_service.py)` |
| Leaderboard | [5](#5-термины-геймификации) | [API → GET /leaderboard](./API.md#leaderboard) |

## Тестирование

| Понятие | Раздел | Документация |
|---------|--------|-------------|
| Unit Tests | [8.7](#unit-tests) | `[tests/unit/](tests/unit/)` |
| Integration Tests | [8.7](#integration-tests) | `[tests/integration/](tests/integration/)` |
| E2E Tests | [8.7](#e2e-tests) | `[tests/e2e/](tests/e2e/)` |
| SAST | [8.4](#sast-static-application-security-testing) | [CICD.md](./CICD.md#security) |

## Фронтенд

| Понятие | Раздел | Документация |
|---------|--------|-------------|
| FSD | [8.8](#fsd-feature-sliced-design) | `[frontend/src/](frontend/src/)` |
| Zustand | [8.8](#zustand) | `[frontend/src/stores/](frontend/src/stores/)` |
| Tailwind CSS | [8.8](#tailwind-css) | `[frontend/tailwind.config.js](frontend/tailwind.config.js)` |
| React | [7](#7-термины-фронтенда) | `[frontend/src/](frontend/src/)` |
| TypeScript | [7](#7-термины-фронтенда) | `[frontend/tsconfig.json](frontend/tsconfig.json)` |
| Vite | [7](#7-термины-фронтенда) | `[frontend/vite.config.ts](frontend/vite.config.ts)` |

---

## 8.9. Протоколы и форматы


### HTTP / REST

| | |
|---|---|
| **Определение** | Протокол передачи данных и архитектурный стиль API. Все endpoint приложения — RESTful HTTP API. |
| **Методы** | GET (чтение), POST (создание), PUT (обновление), DELETE (удаление). PATCH не используется (полная замена ресурса). |
| **Формат** | JSON (request body, response body). Заголовки: `Content-Type: application/json`, `Authorization: Bearer <token>`. |
| **Коды ответов** | 200 OK, 201 Created, 204 No Content, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Validation Error, 429 Too Many Requests, 500 Internal Server Error |
| **Документация** | [API.md](./API.md) |

---

### WebSocket (WSS)

| | |
|---|---|
| **Определение** | Протокол двусторонней связи в реальном времени. |
| **Где используется** | Компонент `SessionWebSocketHandler` для live-сессий: оператор отправляет сообщение → сервер перенаправляет AI-клиенту → AI-клиент отвечает → оператор получает ответ. |
| **Endpoint** | `ws://host/api/ws/session/{session_id}?token={jwt}` (планируется) |
| **Формат сообщений** | JSON: `{"type": "turn", "content": "..."}` |
| **Документация** | [SPECIFICATION.md](./SPECIFICATION.md#nfr) |
| **Связанные понятия** | HTTP, Session, Turn |

---

### JSON (JavaScript Object Notation)

| | |
|---|---|
| **Определение** | Текстовый формат обмена данными, основанный на синтаксисе JavaScript. |
| **Где используется** | Все API запросы/ответы, конфигурационные файлы (`seed/`), структура turn в сессиях. |
| **Библиотека** | `json` (Python stdlib) для бэкенда |
| **Код** | `[src/api/schemas/](src/api/schemas/)` — Pydantic модели сериализации |
| **Связанные понятия** | REST, API, Pydantic |

---

### async / await

| | |
|---|---|
| **Определение** | Механизм асинхронного программирования в Python. |
| **Где используется** | Все I/O операции: HTTP-запросы (httpx), БД-запросы (asyncpg), LLM-вызовы, WebSocket. |
| **Библиотеки** | `asyncio` (stdlib), `asyncpg` (БД), `httpx` (HTTP), `fastapi` (веб-фреймворк) |
| **Код** | `[src/api/routes/](src/api/routes/)` — все endpoint async def |
| **Связанные понятия** | FastAPI, I/O, Event Loop |


## 8.10. Роли и пользователи (детально)


### Trainer

| | |
|---|---|
| **Определение** | Супервайзер, управляющий обучением группы операторов. |
| **Действия** | 1. Создаёт и назначает тренировочные планы 2. Просматривает статистику группы 3. Получает уведомления о проблемных операторах (низкие оценки, пропуски) 4. Создаёт кастомные сценарии через CuratorAgent |
| **Разграничение** | Trainer видит только операторов своей группы. Не имеет доступа к системным настройкам. |
| **Код** | `[src/core/entities/user.py](src/core/entities/user.py)` (role=trainer) |
| **Документация** | [USER_GUIDE.md](./USER_GUIDE.md#trainer) |
| **Связанные понятия** | Operator, Training Plan, CuratorAgent |

---

### Admin

| | |
|---|---|
| **Определение** | Системный администратор, отвечающий за настройку и мониторинг приложения. |
| **Действия** | 1. Управление пользователями (создание, блокировка) 2. Системные настройки (лимиты сессий, провайдеры LLM) 3. Мониторинг (Prometheus + Grafana) 4. Просмотр логов и алертов |
| **Код** | `[src/core/entities/user.py](src/core/entities/user.py)` (role=admin) |
| **Документация** | [ADMIN_GUIDE.md](./ADMIN_GUIDE.md) |
| **Связанные понятия** | RBAC, Prometheus, Grafana |


# Часть III. Тематический указатель
- [API.md](./API.md) — 34 REST endpoint
- [DATA_FLOWS.md](./DATA_FLOWS.md) — use case диаграммы
- [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md) — 17 ADR
- [ADMIN_GUIDE.md](./ADMIN_GUIDE.md) — руководство администратора
- [USER_GUIDE.md](./USER_GUIDE.md) — руководство пользователя
- [DEPLOYMENT_PLAN.md](./DEPLOYMENT_PLAN.md) — план развёртывания
- [CICD.md](./CICD.md) — CI/CD пайплайн
- [src/core/entities/](../src/core/entities/) — доменные сущности
- [src/core/services/](../src/core/services/) — сервисы
- [src/agents/](../src/agents/) — AI-агенты
- [src/infrastructure/](../src/infrastructure/) — инфраструктура
- [frontend/](../frontend/) — исходный код фронтенда
