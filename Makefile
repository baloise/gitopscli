init:
	pip3 install --editable .
	pip3 install -r requirements-dev.txt

format:
	black -l 120 -t py37 gitopscli tests setup.py

lint:
	pylint gitopscli

test:
	python3 -m pytest -v -s

image:
	docker build -t gitopscli:latest .

docs:
	mkdocs serve

.PHONY: init format lint test image docs