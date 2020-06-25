"""The edx_lint check command."""

import os

from edx_lint.tamper_evident import TamperEvidentFile


def check_main(argv):
    """
    check FILENAME
        Check that FILENAME has not been edited since writing.
    """
    if len(argv) != 1:
        print("Please provide the name of a file to check.")
        return 1

    filename = argv[0]

    if os.path.exists(filename):
        print(u"Checking existing copy of %s" % filename)
        tef = TamperEvidentFile(filename)
        if tef.validate():
            print(u"Your copy of %s is good" % filename)
        else:
            print(u"Your copy of %s seems to have been edited" % filename)
    else:
        print(u"You don't have a copy of %s" % filename)

    return 0
