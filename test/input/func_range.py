"""Bad uses of range()."""

import six

if six.PY3:
    def xrange(*args_unused):       # pylint: disable=unused-argument, redefined-builtin
        """Just to keep PY3 happy."""

i = 12

range(0, 10)
range(0, i)
range(0, i, 1)
xrange(0, 10)

# pylint: disable=simplifiable-range
range(0, 1000, 1)
# pylint: enable=simplifiable-range
range(0, 10, 1)
