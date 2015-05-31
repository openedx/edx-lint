"""Bad uses of range()."""

i = 12

range(0, 10)
range(0, i)
range(0, i, 1)
xrange(0, 10)

# pylint: disable=simplifiable-range
range(0, 1000, 1)
# pylint: enable=simplifiable-range
range(0, 10, 1)
