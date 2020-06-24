"""edx_lint pylint module.

Add this to your pylintrc::

    load-plugins=edx_lint.pylint

"""

from edx_lint.pylint import plugin

# Pylint both insists on, and complains about, this name :)
# pylint: disable=invalid-name
register = plugin.register
