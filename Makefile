format:
	black -l 120 -t py37 gitopscli tests setup.py

lint:
	pylint gitopscli

test:
	python3 -m pytest -v -s

install:
	pip3 install -r requirements.txt
	pip3 install -r requirements-dev.txt
	pip3 install --editable .

uninstall:
	pip3 uninstall gitopscli

build:
	docker build -t gitopscli:latest .

docs:
	mkdocs gh-deploy

serve_docs:
	mkdocs serve

.PHONY: format lint test install uninstall build docs serve_docs