# Makefile for edx-lint

.PHONY: default test

default: test

test:
	python test/test_pylint_plugins.py

clean:
	-rm -rf *.egg-info
	-rm -f *.pyc */*.pyc */*/*.pyc */*/*/*.pyc */*/*/*/*.pyc */*/*/*/*/*.pyc
	-rm -rf __pycache__ */__pycache__ */*/__pycache__ */*/*/__pycache__ */*/*/*/__pycache__ */*/*/*/*/__pycache__
	-rm -f MANIFEST
