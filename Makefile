BLACK_ARGS = -l 120 -t py310 gitopscli tests setup.py

init:
	pip3 install --editable .
	pip3 install -r requirements-test.txt
	pip3 install -r requirements-docs.txt
	pre-commit install

format:
	black $(BLACK_ARGS)

format-check:
	black $(BLACK_ARGS) --check

lint:
	pylint gitopscli

mypy:
	python3 -m mypy --install-types --non-interactive .

test:
	python3 -m pytest -vv -s --typeguard-packages=gitopscli

coverage:
	coverage run -m pytest
	coverage html
	coverage report
#temporary mypy test lock
#checks: format-check lint mypy test 
checks: format-check lint test

image:
	DOCKER_BUILDKIT=1 docker build --progress=plain -t gitopscli:latest .

docs:
	mkdocs serve

.PHONY: init format format-check lint mypy test coverage checks image docs
