init:
	uv sync --locked --all-groups
	uv run pre-commit install

format:
	uv run ruff format gitopscli tests
	uv run ruff gitopscli tests --fix

format-check:
	uv run ruff format gitopscli tests --check

lint:
	uv run ruff gitopscli tests

mypy:
	uv run mypy --install-types --non-interactive .


test:
	uv run pytest -vv -s --typeguard-packages=gitopscli

coverage:
	uv run coverage run -m pytest
	uv run coverage html
	uv run coverage report

checks: format-check lint mypy test

image:
	DOCKER_BUILDKIT=1 docker build --progress=plain -t gitopscli:latest .

docs:
	uv run mkdocs serve

update:
	uv lock

.PHONY: init format format-check lint mypy test coverage checks image docs update
