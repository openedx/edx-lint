Adding New Checks
=================

Status
------

Draft

Context
-------

When adding new violations to edx-lint, there currently isn't clarity around the following:

* What changes should be considered a breaking change, requiring a major version bump.
* Are there ways to avoid too many breaking changes.
* When and where to best communicate changes.
* How to ensure that settings for new violations are being picked up by repositories.

Decisions
---------

* New checks should be considered breaking changes. See `how_tos/0001-adding-new-checks.rst` for more details around properly updating the changelog.
* To avoid breaking changes, new plugins can be added as optional when first launched. See `how_tos/0001-adding-new-checks.rst` for more details.
* Breaking changes will be communicated via a major version bump in the library. We may end up having many of these.
* We would like to add automation to upgrade the pylintrc file in each repo with changes made in edx-lint.

Consequences
------------

* Update documentation of the results of this decision.
* Create automation capabilities for updating pylintrc files in repos. This will required additional discovery around the best way to handle this.
