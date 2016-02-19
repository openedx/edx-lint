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

# no message when variables are involved
START, STOP, STEP = 0, 10, 1
range(START, 100)
range(START, STOP)
range(0, 10, STEP)

# if it has four arguments, we don't know what's going on...
range(0, 10, 1, "something")
