Adding New Checks
=================

Status
------

Draft

Context
-------

When adding new violations to edx-lint, there currently isn't clarity around the following:

* What changes should be considered a breaking change, requiring a major version bump.
* How to avoid too avoid many breaking changes.
* When and where to best communicate changes.
* How to ensure that new violations are being picked up by repositories.

Decisions
---------

* New checks should be introduced as optional, even if you ultimately want them to be required by default.

  * For rolling out new required-by-default checks, making checks optional at first enables repo owners to fix or amnesty violations on their own timeline before they become required, or batch fixing or amnestying larger batches of checks when they become required.
  * See `how_tos/0001-adding-new-checks.rst` for details in making this happen.

* Mark new checks that will become required as deprecated as disabled/optional checks.
* Communicate new disabled/optional checks that will be required-by-default in the future.
* Use a major version bump when making a group of checks required-by-default. The major version should be enough for communication.
* Add automation to upgrade the pylintrc file in each repo with changes made in edx-lint.

Consequences
------------

* Update documentation of the results of this decision.
* Create automation capabilities for updating pylintrc files in repos.
