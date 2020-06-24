"""The edx_lint command."""

import sys

from edx_lint.cmd.check import check_main
from edx_lint.cmd.list import list_main
from edx_lint.cmd.write import write_main


def main(argv=None):
    """The edx_lint command entry point."""
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] == "help":
        show_help()
        return 0
    elif argv[0] == "check":
        return check_main(argv[1:])
    elif argv[0] == "list":
        return list_main(argv[1:])
    elif argv[0] == "write":
        return write_main(argv[1:])
    else:
        print(u"Don't understand {!r}".format(" ".join(argv)))
        show_help()
        return 1


def show_help():
    """Print the help string for the edx_lint command."""
    print(
        """\
Manage local config files from masters in edx_lint.

Commands:
"""
    )
    for cmd in [write_main, check_main, list_main]:
        print(cmd.__doc__.lstrip("\n"))
