"""
Information about the files we can write.
"""

import dataclasses

@dataclasses.dataclass
class Metadata:
    format: str
    comment: str
    internal_only: bool = False


KNOWN_FILES = {
    "pylintrc": Metadata(
        format="ini",
        comment="# {}",
    ),
    ".editorconfig": Metadata(
        format="ini",
        comment="# {}",
    ),
    "commitlint.config.js": Metadata(
        format="js",
        comment="// {}",
    ),

    "just_for_testing.txt": Metadata(
        format="txt",
        comment="-- {}",
        internal_only=True,
    ),
    # BTW: common_constraints.txt is in the resources, but isn't a file
    # that edx_lint writes.
}
