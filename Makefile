# Makefile for edx-lint

.PHONY: default test

default: test

test:
	tox -e py27-pylint17,py36-pylint17,coverage

pylint:
	tox -e pylint

clean:
	-rm -rf .tox
	-rm -rf *.egg-info
	-find . -name '__pycache__' -prune -exec rm -rf "{}" \;
	-find . -name '*.pyc' -delete
	-rm -f MANIFEST
	-rm -rf .coverage .coverage.* htmlcov

requirements:
	pip install -r requirements/dev.txt

upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: ## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	pip install -qr requirements/pip-tools.txt
	# Make sure to compile files after any other files they include!
	pip-compile -v --upgrade -o requirements/pip-tools.txt requirements/pip-tools.in
	pip-compile -v --upgrade -o requirements/dev.txt requirements/dev.in
