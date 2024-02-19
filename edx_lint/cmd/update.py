"""The edx_lint update command: write any file that exists."""

from edx_lint.write import write_file
from edx_lint.metadata import existing_known_files

def update_main(argv_unused):  # pylint: disable=unused-argument
    """
    update
        Re-write any edx_lint-written files that exists on disk.
    """

    for filename in existing_known_files():
        ret = write_file(filename, output_fn=print)
        if ret != 0:
            return ret
    return 0
