==========
Change Log
==========
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

..
    Feel free to update the following link to actual changelog entries.
..

* Here is a `link to additional commits`_ that may or may not warrant changelog entries, but were committed before reminding developers to update the changelog.

.. _link to additional commits: https://github.com/edx/edx-lint/compare/1.5.2...a29f286

[1.5.2] - 2020-08-20
~~~~~~~~~~~~~~~~~~~~

Added
_____

* Add global constraint file. A central location for most common version constraints (across edx repos) for pip-installation.

[1.5.0] - 2020-06-30
~~~~~~~~~~~~~~~~~~~~

Added
_____

* Added support for Python 3.8

Fixed
_____

* Fixed: the .editorconfig file was not installed, and so was not writable.

Removed
_______

* Breaking: dropped support for Python 2.
* Pylintrc: dropped code scoring.

Older versions
~~~~~~~~~~~~~~

Older versions were documented as `Github releases`_ only.

.. _Github releases: https://github.com/edx/edx-lint/releases
