# Makefile for edx-lint

.PHONY: clean help pylint requirements test upgrade

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

test: ## run all the tests
	tox -e py38-pylint24,coverage

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
	pip install -qr requirements/pip.txt
	pip install -e .
	pip install -r requirements/dev.txt

compile-requirements: export CUSTOM_COMPILE_COMMAND=make upgrade
compile-requirements: ## compile the requirements/*.txt files with the latest packages satisfying requirements/*.in
	# Make sure to compile files after any other files they include!
	pip-compile -v --allow-unsafe --rebuild -o requirements/pip.txt requirements/pip.in
	pip-compile -v ${COMPILE_OPTS} -o requirements/pip-tools.txt requirements/pip-tools.in
	pip-compile -v ${COMPILE_OPTS} -o requirements/base.txt requirements/base.in
	pip-compile -v ${COMPILE_OPTS} -o requirements/dev.txt requirements/dev.in
	pip-compile -v ${COMPILE_OPTS} -o requirements/test.txt requirements/test.in
	pip-compile -v ${COMPILE_OPTS} -o requirements/ci.txt requirements/ci.in

upgrade: ## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	pip install -qr requirements/pip-tools.txt
	$(MAKE) compile-requirements COMPILE_OPTS="--upgrade"
