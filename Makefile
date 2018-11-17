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
	pip install -r dev-requirements.txt
