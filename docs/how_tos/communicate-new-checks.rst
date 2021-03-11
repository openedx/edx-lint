How-To: Communicate New Lint Plugins or Checks
==============================================

Adding a new lint plugin
------------------------

After coding a new lint plugin, it should start off being optional, even if you intend to make it required-by-default in the future. See decisions/0001-adding-new-checks.rst for background on why.

If all checks in the plugin will always be optional, simply provide instructions in the CHANGELOG.rst for how to add the plugin. For example::

  * Explain the purpose of the new plugin, and potentially list its new checks.
  * To use the ``example_plugin`` plugin, you should follow the "LOCAL CHANGES" instructions in pylintrc to add it:

    .. code-block:: python

        load-plugins=edx_lint.pylint.example_plugin

If any checks in the plugin are meant to become required-by-default in the future:

* Follow the instructions in the pylintrc file for making a "CENTRAL CHANGE".

  * Add the plugin to ``load-plugins`` as detailed above in pylintrc.
  * Ensure all new checks are added under the disable list, and not the enable list in pylintrc.

* Add the new CHANGELOG.rst entry:

  * Explain the purpose of the new plugin and list its new checks.
  * List any new checks that will become required-by-default under a "Deprecated" section, noting the fact that they are disabled is deprecated, and they will be required/enabled by default, in a future major release.

* Communicate that there will be new required checks in the future. Consider providing a proposed date, which may be a shared date for other deprecated checks added in the past. See `Requiring new checks`_ for details.

Adding a new lint check
-----------------------

After coding a new check, it should start off being optional.

Generally follow the same instructions regarding checks detailed under `Adding a new lint plugin`_, skipping any details about plugins.

Requiring new checks
--------------------

Some time after checks have been added as optional (see `Adding a new lint check`_), you may be ready to make them required by default. It would be best to require new checks in bulk, so try to coordinate to reduce the number of breaking changes.

* Use a major version bump to communicate breaking changes.
* Follow the instructions in the pylintrc file for making a "CENTRAL CHANGE".

  * Move optional checks from the disable list to the enable list in pylintrc.

* Add a CHANGELOG.rst entry noting the breaking change(s).

  * List the checks that are now required-by-default.
  * Note that violations of the new checks can either be fixed, or amnestied following instructions in the README.
  * If instructions for fixing the new checks is not clear from the check's message, add a link to any additional documentation required to fix.
