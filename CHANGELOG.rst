Change Log
----------
..
   All enhancements and patches to edx-lint will be documented
   in this file.  It adheres to the structure of http://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).
   This project adheres to Semantic Versioning (http://semver.org/).
   There should always be an "Unreleased" section for changes pending release.
..

Unreleased
~~~~~~~~~~


[1.5.0] - 2020-06-30
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Breaking: dropped support for Python 2.
* Pylintrc: dropped code scoring.
* Fixed: the .editorconfig file was not installed, and so was not writable.
* Added support for Python 3.8
