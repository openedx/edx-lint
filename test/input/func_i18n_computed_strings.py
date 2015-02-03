"""These are bad uses of _()"""

# pylint: disable=missing-docstring

from string import lower as _

def welcome(name):
    _("Hello"+"There")
    _(17)
    _("Hi, {0}".format(name))
