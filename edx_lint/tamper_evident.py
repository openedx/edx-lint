"""Tamper-evident text files."""

import hashlib
import re


class TamperEvidentFile(object):
    """Tamper-evident files.

    Write text to a file with `.write()`.  Later, you can validate that it
    hasn't changed with `.validate()`.

    """

    def __init__(self, filename):
        self.filename = filename

    def write(self, text, hashline=u"# {}"):
        """
        Write `text` to the file.

        Writes the text to the file, with a final line checksumming the
        contents.  The entire file must be written with one `.write()` call.

        The last line is written with the `hashline` format string, which can
        be changed to accommodate different file syntaxes.

        Arguments:
            text (unicode string): the contents of the file to write.

            hashline (unicode string): the format of the last line to append to
                the file, with "{}" replaced with the hash.

        """
        if not text.endswith(u"\n"):
            text += u"\n"

        hash = hashlib.sha1(text.encode("ascii")).hexdigest()

        with open(self.filename, "w") as f:
            f.write(text)
            f.write(hashline.format(hash))
            f.write(u"\n")

    def validate(self):
        """
        Check if the file still has its original contents.

        Returns True if the file is unchanged, False if it has been tampered
        with.
        """

        with open(self.filename, "r") as f:
            text = f.read()

        start_last_line = text.rfind(u"\n", 0, -1)
        if start_last_line == -1:
            return False

        original_text = text[:start_last_line+1]
        last_line = text[start_last_line+1:]

        expected_hash = hashlib.sha1(original_text).hexdigest().encode("ascii")
        match = re.search(r"[0-9a-f]{40}", last_line)
        if not match:
            return False
        actual_hash = match.group(0)
        if actual_hash != expected_hash:
            return False
        return True
