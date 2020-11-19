BLACK_ARGS = -l 120 -t py37 gitopscli tests setup.py

init:
	pip3 install --editable .
	pip3 install -r requirements-dev.txt

format:
	black $(BLACK_ARGS)

format-check:
	black $(BLACK_ARGS) --check

lint:
	pylint gitopscli

test:
	python3 -m pytest -vv -s

coverage:
	coverage run -m pytest
	coverage html
	coverage report

checks: format-check lint test

image:
	docker build -t gitopscli:latest .

docs:
	mkdocs serve

.PHONY: init format format-check lint test coverage checks image docs