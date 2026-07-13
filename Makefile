.PHONY: install lint format typecheck test docker-up docker-down clean

install:
	pip install -e ".[dev]"

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/

test:
	pytest tests/ -q --tb=short

test-cov:
	pytest tests/ --cov=src --cov-report=term-missing

docker-up:
	docker compose -f docker-compose.dev.yml up -d

docker-down:
	docker compose -f docker-compose.dev.yml down

docker-logs:
	docker compose -f docker-compose.dev.yml logs -f

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache __pycache__
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
