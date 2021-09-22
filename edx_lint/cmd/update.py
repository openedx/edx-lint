"""The edx_lint update command: write any file that exists."""

import os.path

from edx_lint.write import write_file
from edx_lint.metadata import KNOWN_FILES

def update_main(argv_unused):  # pylint: disable=unused-argument
    """
    update
        Re-write any edx_lint-written files that exists on disk.
    """
    for filename, metadata in KNOWN_FILES.items():
        if metadata.internal_only:
            continue
        if os.path.exists(filename):
            ret = write_file(filename, output_fn=print)
            if ret != 0:
                return ret
    return 0
