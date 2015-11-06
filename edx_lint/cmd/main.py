"""The edx_lint command."""
from __future__ import print_function

import sys

from edx_lint.cmd.check import check_main
from edx_lint.cmd.list import list_main
from edx_lint.cmd.write import write_main


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] == "help":
        help()
    elif argv[0] == "check":
        return check_main(argv[1:])
    elif argv[0] == "list":
        return list_main(argv[1:])
    elif argv[0] == "write":
        return write_main(argv[1:])
    else:
        print("Don't understand {!r}".format(" ".join(argv)))
        help()


def help():
    print("""\
Manage local config files from masters in edx_lint.

Commands:
    write FILENAME
        Write a local copy of FILENAME using FILENAME_tweaks for local tweaks.

    check FILENAME
        Check that FILENAME has not been edited since writing.

    list
        List the FILENAMEs that edx_lint can provide.
""")
