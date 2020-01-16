format:
	black -l 120 -t py37 gitopscli

install:
	pip3 install -r requirements.txt
	pip3 install --editable .

uninstall:
	pip3 uninstall gitopscli

build:
	docker build -t gitopscli:latest .

.PHONY: format install uninstall, build