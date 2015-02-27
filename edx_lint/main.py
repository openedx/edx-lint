"""The edx_lint command."""

import sys

from edx_lint.write import write


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if argv[0] == "write":
        return write(argv[1:])
