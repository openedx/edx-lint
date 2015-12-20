# Makefile for edx-lint

.PHONY: default test

default: test

test:
	python -m unittest discover

coverage:
	coverage run -m unittest discover
	coverage report -m

pylint:
	pylint edx_lint test setup.py

clean:
	-rm -rf *.egg-info
	-find . -name '__pycache__' -prune -exec rm -rf "{}" \;
	-find . -name '*.pyc' -delete
	-rm -f MANIFEST
	-rm -rf .coverage .coverage.* htmlcov

requirements:
	pip install -r dev-requirements.txt
