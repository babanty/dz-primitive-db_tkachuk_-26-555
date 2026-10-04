.PHONY: install run lint format test build check

install:
	uv sync

run:
	uv run database

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run python -m unittest discover -s tests -v

build:
	uv build

check: lint test
