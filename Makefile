.PHONY: install generate train test lint typecheck quality smoke compile docker-up docker-smoke docker-down

install:
	python -m pip install -e ".[quality]"

generate:
	python -m sentinelflow.cli generate --output data/raw/transactions.csv --rows 5000 --seed 42

train: generate
	python -m sentinelflow.cli train --data data/raw/transactions.csv --registry model-registry

test:
	pytest

lint:
	ruff check src tests scripts pipelines

typecheck:
	mypy src

quality: lint typecheck test compile

smoke:
	python scripts/smoke_test.py

compile:
	python -m compileall -q src tests pipelines scripts

docker-up:
	docker compose -f infra/docker/docker-compose.yml up --build -d

docker-smoke:
	python scripts/docker_smoke.py

docker-down:
	docker compose -f infra/docker/docker-compose.yml down
