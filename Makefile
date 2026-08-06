# Makefile for edx-lint

.PHONY: clean help pylint requirements test upgrade

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

test: ## run all the tests
	uv run --group test pytest

pylint: ## check our own code with pylint
	uv run --group quality pylint src/edx_lint test

clean: ## remove all the unneeded artifacts
	-rm -rf .tox
	-rm -rf *.egg-info
	-find . -name '__pycache__' -prune -exec rm -rf "{}" \;
	-find . -name '*.pyc' -delete
	-rm -f MANIFEST
	-rm -rf .coverage .coverage.* htmlcov

requirements: ## install the developer requirements
	uv sync --group dev

upgrade: ## update the lockfile with the latest packages satisfying constraints
	uv run --with edx-lint edx_lint write_uv_constraints pyproject.toml
	uv lock --upgrade
