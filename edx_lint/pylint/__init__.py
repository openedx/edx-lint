"""edx_lint pylint module.

Add this to your pylintrc::

    load-plugins=edx_lint.pylint

"""

from edx_lint.pylint import plugin

register = plugin.register
