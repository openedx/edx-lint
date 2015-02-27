"""The edx_lint command."""

import sys

from edx_lint.check import check_main
from edx_lint.list import list_main
from edx_lint.write import write_main


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if argv[0] == "check":
        return check_main(argv[1:])
    elif argv[0] == "list":
        return list_main(argv[1:])
    elif argv[0] == "write":
        return write_main(argv[1:])
