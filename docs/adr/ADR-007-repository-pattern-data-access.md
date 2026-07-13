# ADR-007: Repository Pattern для доступа к данным

**Статус:** Принято

**Дата:** 2026-07-12

## Контекст

Приложение поддерживает как in-memory, так и PostgreSQL режимы. Переключение между ними должно быть прозрачным для сервисов и контроллеров. Слой доступа к данным должен быть тестируемым без внешних зависимостей.

## Решение

Принять **Repository Pattern**:

```
Controller/Service → Interface (ABC) → InMemoryRepository | PostgresRepository
```

### Интерфейс
```python
class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User: ...
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User: ...
    @abstractmethod
    async def get_by_username(self, username: str) -> User | None: ...
    @abstractmethod
    async def list_all(self) -> list[User]: ...
```

### Конкретные реализации
| Repository | In-Memory | PostgreSQL |
|------------|-----------|------------|
| UserRepository | `[src/infrastructure/memory/repositories.py](src/infrastructure/memory/repositories.py)` | `[src/infrastructure/postgres/user_repo.py](src/infrastructure/postgres/user_repo.py)` |
| SessionRepository | `[src/infrastructure/memory/repositories.py](src/infrastructure/memory/repositories.py)` | `[src/infrastructure/postgres/session_repo.py](src/infrastructure/postgres/session_repo.py)` |
| ScenarioRepository | `[src/infrastructure/memory/repositories.py](src/infrastructure/memory/repositories.py)` | `[src/infrastructure/postgres/scenario_repo.py](src/infrastructure/postgres/scenario_repo.py)` |
| XpTransactionRepository | `[src/infrastructure/memory/repositories.py](src/infrastructure/memory/repositories.py)` | `[src/infrastructure/postgres/xp_transaction_repo.py](src/infrastructure/postgres/xp_transaction_repo.py)` |
| EvaluationRepository | `[src/infrastructure/memory/repositories.py](src/infrastructure/memory/repositories.py)` | `[src/infrastructure/postgres/evaluation_repo.py](src/infrastructure/postgres/evaluation_repo.py)` |
| TrainingPlanRepository | `[src/infrastructure/memory/repositories.py](src/infrastructure/memory/repositories.py)` | `[src/infrastructure/postgres/training_plan_repo.py](src/infrastructure/postgres/training_plan_repo.py)` |

### Выбор реализации
- `DB_MODE=memory` → inject InMemoryRepository
- `DB_MODE=postgres` → inject PostgresRepository
- Выбор происходит в `dependencies.py`

## Рассмотренные альтернативы

- **Active Record (SQLAlchemy модели напрямую):** Привязало бы сервисы к SQL — отклонено ради тестируемости.
- **Django ORM:** Слишком тяжёл для FastAPI проекта — отклонено.
- **Raw SQL везде:** Непортативно между режимами — отклонено.
- **Data Mapper с SQLAlchemy:** Рабочий вариант, но добавляет сложность — отложено до необходимости.

## Последствия

- **Положительно:** Сервисы никогда не знают, какой режим хранения активен
- **Положительно:** In-memory репозитории в тестах = не требуется настройка БД
- **Положительно:** Легко добавить новые бэкенды хранения (например, MongoDB, Redis)
- **Отрицательно:** Шаблонный код — каждый метод нужно реализовать дважды
- **Отрицательно:** PostgreSQL репозитории должны синхронизироваться с поведением in-memory
