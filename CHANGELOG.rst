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

[4.1.0] - 2021-02-24
~~~~~~~~~~~~~~~~~~~~

Added unittest_assert module (optional plugin for unittest assertion checks)

To use this plugin, you should add this to your pylintrc

.. code-block:: python

    load-plugins=edx_lint.pylint.unittest_assert

[4.0.1] - 2021-02-04
~~~~~~~~~~~~~~~~~~~~

edx-lint will now ignore the logging-fstring-interpolation warning in pylint.

[4.0.0] - 2021-01-28
~~~~~~~~~~~~~~~~~~~~

* BREAKING CHANGE: modify the numerical ID of annotation checks
* BREAKING CHANGES:

  * modify the numerical ID of annotation checks
  * though technically not a breaking change, the new annotation checks may break your build if there are pre-existing
    violations.

* Add ``CodeAnnotationChecker`` to run generic checks on annotations

[3.0.2] - 2021-01-26
~~~~~~~~~~~~~~~~~~~~

* Fix line number from annotation checks.

[3.0.1] - 2021-01-26
~~~~~~~~~~~~~~~~~~~~

* Added constraints file to handle package versions.

[3.0.0] - 2021-01-24
~~~~~~~~~~~~~~~~~~~~

* Add setting annotation linting.
* Add feature toggle annotation linting.

[2.0.0] - 2021-01-21
~~~~~~~~~~~~~~~~~~~~

* Drop support for Python 3.5

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
