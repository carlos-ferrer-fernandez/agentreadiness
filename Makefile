.PHONY: help install dev build test clean docker-up docker-down

help:
	@echo "AgentReadiness Platform - Available commands:"
	@echo ""
	@echo "  make install      - Install all dependencies"
	@echo "  make dev          - Start development servers"
	@echo "  make build        - Build production assets"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"
	@echo ""

install:
	@echo "Installing frontend dependencies..."
	cd apps/web && npm install
	@echo "Installing backend dependencies..."
	cd apps/api && pip install -r requirements.txt

dev:
	@echo "Starting development servers..."
	make dev-api & make dev-web

dev-web:
	cd apps/web && npm run dev

dev-api:
	cd apps/api && uvicorn main:app --reload --port 8000

build:
	@echo "Building frontend..."
	cd apps/web && npm run build

test:
	@echo "Running frontend tests..."
	cd apps/web && npm test
	@echo "Running backend tests..."
	cd apps/api && pytest

clean:
	@echo "Cleaning build artifacts..."
	rm -rf apps/web/dist
	rm -rf apps/web/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down

docker-logs:
	docker-compose logs -f

# Database commands
db-migrate:
	cd apps/api && alembic upgrade head

db-reset:
	docker-compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS agentreadiness;"
	docker-compose exec db psql -U postgres -c "CREATE DATABASE agentreadiness;"
