init:
	poetry install
	pre-commit install

format:
	poetry run ruff format gitopscli tests
	poetry run ruff gitopscli tests --fix

format-check:
	poetry run ruff format gitopscli tests --check

lint:
	poetry run ruff gitopscli tests

mypy:
	poetry run mypy --install-types --non-interactive .


test:
	poetry run pytest -vv -s --typeguard-packages=gitopscli

coverage:
	coverage run -m pytest
	coverage html
	coverage report

checks: format-check lint mypy test

image:
	DOCKER_BUILDKIT=1 docker build --progress=plain -t gitopscli:latest .

docs:
	mkdocs serve

update:
	poetry lock

.PHONY: init format format-check lint mypy test coverage checks image docs update
