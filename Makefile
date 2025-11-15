.PHONY: help install test lint format check clean dev server

help:
	@echo "FirstShift API Gateway SDK - Development Commands"
	@echo ""
	@echo "make install    - Install dependencies"
	@echo "make test       - Run tests"
	@echo "make lint       - Run linting checks"
	@echo "make format     - Format code"
	@echo "make check      - Run all checks (lint + test)"
	@echo "make clean      - Clean build artifacts"
	@echo "make dev        - Install in development mode"
	@echo "make server     - Start FastAPI server"

install:
	uv sync

dev:
	uv sync --dev
	uv pip install -e .

test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ --cov=fsgw --cov-report=html --cov-report=term-missing

lint:
	uv run ruff check fsgw/
	uv run mypy fsgw/

format:
	uv run ruff format fsgw/ tests/

check: lint test

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

server:
	uv run python -m fsgw.server.main
