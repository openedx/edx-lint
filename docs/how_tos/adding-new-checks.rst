How-To: Adding New Lint Plugins or Checks
==============================================

Adding a new lint check
-----------------------

Most new lint checks will automatically be enabled and active in any repository using edx-lint. It would be best to consider this a breaking change, because it will require developers that are upgrading edx-lint to take action.

* Use a major version bump to communicate breaking changes.
* Add a CHANGELOG.rst entry noting the breaking change(s):

  * List the new checks that were added as a BREAKING CHANGE.
  * Note that the edx-lint README provides options for handling newly introduced violations.
  * If additional instructions might be required for fixing the new checks, add a link to any supporting documentation.

Note: even if you want the new check(s) to be opt-in, it will still be a breaking change because developers will need to take action. In this case, you would need to do the following:

* Use the CENTRAL CHANGE instructions to add the check as disabled in the pylintrc file.
* Use a major version bump to communicate breaking changes.
* Add a CHANGELOG.rst entry noting the breaking change(s):

  * List the new checks that were added as a BREAKING CHANGE.
  * Tell developers to follow the README for `pylint_tweaks` to enable the checks if they wish to opt-in.
  * Explain that whether or not they wish to opt-in, they will need to write an updated pylintrc file to have an accurate configuration.

Adding an optional plugin
-------------------------

Most new checks are included by default with edx-lint. However, it is possible to make a new lint plugin that is optional. Here is an example of `an optional plugin introduced as a subpackage`_. In this case, you would only use a minor version bump.

Additional notes:

* Any future lint checks added to an optional plugin should follow the same process detailed under `Adding a new lint check`_, because anyone may have already enabled the optional plugin and will automatically get any new checks.
* If an optional plugin should later become a default plugin, we don't yet have clear guidance on whether to simply add the plugin as a new default, or move its implementation to the main package. In either case, this would be considered a breaking change.

.. _an optional plugin introduced as a subpackage: https://github.com/openedx/edx-lint/pull/144/files
