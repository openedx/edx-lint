"""Good uses of range."""

import six

if six.PY3:
    def xrange(*args_unused):       # pylint: disable=unused-argument, redefined-builtin
        """Just to keep PY3 happy."""


i = 2

range(10)
range(i)
range(1, 10)
range(1, 10, 2)
range(i, 10)
range(0, 10, 2)
xrange(10)
xrange(i)
xrange(1, 10)
xrange(1, 10, 2)
xrange(i, 10)
xrange(0, 10, 2)
