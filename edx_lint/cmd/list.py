"""The edx_lint list command."""

import pkg_resources


def list_main(argv_unused):
    print "edx_lint knows about these files:"
    for filename in pkg_resources.resource_listdir("edx_lint", "files"):
        print filename

    return 0
