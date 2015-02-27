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
	-rm -f *.pyc */*.pyc */*/*.pyc */*/*/*.pyc */*/*/*/*.pyc */*/*/*/*/*.pyc
	-rm -rf __pycache__ */__pycache__ */*/__pycache__ */*/*/__pycache__ */*/*/*/__pycache__ */*/*/*/*/__pycache__
	-rm -f MANIFEST
