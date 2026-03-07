# Frontend commands
frontend-install:
	cd frontend/app && npm install

frontend-format:
	cd frontend/app && npm run format

frontend-format-check:
	cd frontend/app && npm run format:check

frontend-lint:
	cd frontend/app && npm run lint

frontend-lint-fix:
	cd frontend/app && npm run lint:fix

frontend-test:
	cd frontend/app && npm test

# Backend commands
backend-install:
	cd backend/app && pip install -r requirements.txt

backend-format:
	cd backend/app && black . && isort .

backend-format-check:
	cd backend/app && black --check . && isort --check-only . && flake8 .

backend-test:
	cd backend && PYTHONPATH=app pytest -v

# ML commands  
ml-install:
	cd ml && pip install -r requirements.txt

ml-format:
	cd ml && black . && isort .

ml-format-check:
	cd ml && black --check . && isort --check-only . && flake8 .

ml-test:
	cd ml && PYTHONPATH=.. pytest -v

# Combined commands
install-all: frontend-install backend-install ml-install

format-all: frontend-format backend-format ml-format

format-check-all: frontend-format-check backend-format-check ml-format-check

lint-all: frontend-lint backend-format-check ml-format-check

test-all: frontend-test backend-test ml-test

# Docker commands
docker-up:
	docker compose -f infra/docker-compose.yml up

docker-up-build:
	docker compose -f infra/docker-compose.yml up --build

docker-down:
	docker compose -f infra/docker-compose.yml down

docker-prod-up:
	docker compose -f docker/docker-compose.yaml up --build

.PHONY: frontend-install frontend-format frontend-format-check frontend-lint frontend-lint-fix frontend-test backend-install backend-format backend-format-check backend-test ml-install ml-format ml-format-check ml-test install-all format-all format-check-all lint-all test-all docker-up docker-up-build docker-down docker-prod-up
