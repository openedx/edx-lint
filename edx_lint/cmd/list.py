"""The edx_lint list command."""

from edx_lint.metadata import KNOWN_FILES


def list_main(argv_unused):  # pylint: disable=unused-argument
    """
    list
        List the files that edx_lint can provide.
    """
    print("edx_lint knows about these files:")
    for filename, metadata in KNOWN_FILES.items():
        if not metadata.internal_only:
            print(f"  {filename}")

    return 0
