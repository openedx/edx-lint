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

5.4.0 - 2024-08-23
~~~~~~~~~~~~~~~~~~

* Added support for python 3.12
* Drop support for python 3.8
* Replaced pkg_resources with importlib.resources

5.3.7 - 2024-07-15
~~~~~~~~~~~~~~~~~~

* Remove support for writing commitlint.config.js files since we don't want
  people to be doing this.

5.3.5 - 2023-04-29
~~~~~~~~~~~~~~~~~~

* added support for pylint 3

5.3.2 - 2023-02-15
~~~~~~~~~~~~~~~~~~

* Removed pylint<2.15 constraint and updated tests for new version
* Removed CI tests for old pylint versions

5.3.1 - 2023-02-14
~~~~~~~~~~~~~~~~~~

* Disabled new warning from pylint 2.16.0: broad-exception-raised

5.3.0 - 2022-09-15
~~~~~~~~~~~~~~~~~~

* Improvements to the ``check`` command:

  - It now exits with a failure status if something is wrong.
  - With no file name arguments, it will check all of your files that edx_lint
    can write.
  - The messages are less chatty.

5.2.5 - 2022-09-08
~~~~~~~~~~~~~~~~~~

* Updated GitHub references from the ``edx`` GitHub organization to ``openedx``.

5.2.4 - 2022-06-10
~~~~~~~~~~~~~~~~~~

* Updated `pylintrc` template for `edx_lint write pylintrc` command for `pylint>=2.14.0`.

5.2.3 - 2022-06-09
~~~~~~~~~~~~~~~~~~

* Removed support of LegacyWaffle* checks, since the classes no longer exist.
* Removed deleted pylint messages from common pylintrc file

5.2.2 - 2022-03-25
~~~~~~~~~~~~~~~~~~

* fixed import path of a pylint protected function to make
  edx-lint compatible with `pylint==2.13.0`.
* Updated testenvs in both tox and CI

5.2.1 - 2021-10-26
~~~~~~~~~~~~~~~~~~

* Include constraint files when generating requirements metadata

5.2.0 - 2021-09-24
~~~~~~~~~~~~~~~~~~

* Silence the "consider-using-f-string" pylint violation.

* The new "update" command will write all edx-lint-writable files that exist
  on disk.

* edx-lint can now write commitlint.config.js files.

* The help message now includes the version.

5.1.0 - 2021-09-01
~~~~~~~~~~~~~~~~~~

* Disabled two new warnings from pylint 2.10: unspecified-encoding and
  use-maxsplit-arg.

[5.0.0] - 2021-03-18
~~~~~~~~~~~~~~~~~~~~

* BREAKING CHANGE: Add linter for invalid imports from Django Waffle (`import waffle` and `from waffle import ...`). Instead, developers should import toggle objects from `edx_toggles.toggles`.
* BREAKING CHANGE: Add linter for missing feature toggle annotations ("toggle-missing-annotation"). Check `this howto <https://edx.readthedocs.io/projects/edx-toggles/en/latest/how_to/documenting_new_feature_toggles.html>`__ for more information on writing toggle annotations.
* Fix duplicate annotation errors.

[4.1.1] - 2021-03-16
~~~~~~~~~~~~~~~~~~~~

* Fixed lint amnesty breakage on line continuation

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

.. _link to additional commits: https://github.com/openedx/edx-lint/compare/1.5.2...a29f286

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

.. _Github releases: https://github.com/openedx/edx-lint/releases
