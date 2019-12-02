# Makefile for edx-lint

.PHONY: clean help pylint requirements test upgrade

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

test: ## run all the tests
	tox -e py35-pylint17,py36-pylint17,coverage

pylint: ## check our own code with pylint
	tox -e pylint

clean: ## remove all the unneeded artifacts
	-rm -rf .tox
	-rm -rf *.egg-info
	-find . -name '__pycache__' -prune -exec rm -rf "{}" \;
	-find . -name '*.pyc' -delete
	-rm -f MANIFEST
	-rm -rf .coverage .coverage.* htmlcov

requirements: ## install the developer requirements
	pip install -r requirements/dev.txt

upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: ## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	pip install -qr requirements/pip-tools.txt
	# Make sure to compile files after any other files they include!
	pip-compile -v --upgrade -o requirements/pip-tools.txt requirements/pip-tools.in
	pip-compile -v --upgrade -o requirements/dev.txt requirements/dev.in
	@echo "\e[31mpylint, pylint-django, and pylint-celery are not managed by make upgrade. Please upgrade them manually in setup.cfg\e[0m"


black:
	black --line-length 120 .

black-test:
	black --line-length 120 --check .
