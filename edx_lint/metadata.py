"""
Information about the files we can write.
"""

import dataclasses

@dataclasses.dataclass
class Metadata:
    format: str
    comment: str


KNOWN_FILES = {
    "pylintrc": Metadata(
        format="ini",
        comment="# {}",
    ),
    ".editorconfig": Metadata(
        format="ini",
        comment="# {}",
    ),
    "just_for_testing.txt": Metadata(
        format="txt",
        comment="-- {}",
    ),
}
