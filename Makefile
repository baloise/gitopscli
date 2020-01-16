format:
	black -l 120 -t py37 gitopscli

install:
	pip3 install -r requirements.txt
	pip3 install --editable .

uninstall:
	pip3 uninstall gitopscli

.PHONY: format install uninstall