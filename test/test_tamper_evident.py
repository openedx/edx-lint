"""Test the TamperEvidentFile class."""

import os
import tempfile
import unittest

from edx_lint.tamper_evident import TamperEvidentFile


class TamperEvidentFileTest(unittest.TestCase):
    """Tests for TamperEvidentFile."""

    def temp_filename(self):
        """
        Make a temporary filename that will be deleted after the test.

        Returns:
            The name of the temp file.

        """
        fdesc, filename = tempfile.mkstemp(suffix=".txt", prefix="tamper_evident_")
        os.close(fdesc)
        self.addCleanup(os.remove, filename)
        return filename

    def write_tamper_evident(self, text, **kwargs):
        """
        Helper to write a tamper-evident temp file.

        Args:
            text (byte string): the content of the file.

            kwargs: any other arguments to `TamperEvidentFile.write`.

        Returns:
            The name of the temp file.

        """
        filename = self.temp_filename()
        TamperEvidentFile(filename).write(text, **kwargs)
        return filename

    def test_writing(self):
        # The contents are written, with a hash.
        # Different contents produce different hashes.
        filename1 = self.write_tamper_evident(b"Hello!")

        with open(filename1, "rb") as f:
            self.assertEqual(f.read(), b"Hello!\n# a8d191538209e335154750d2df575b9ddfb16fc7\n")

        filename2 = self.write_tamper_evident(b"Hello?")

        with open(filename2, "rb") as f:
            self.assertEqual(f.read(), b"Hello?\n# 4820175d44ef1a2c92e52bd1b3b7f05020d66e1c\n")

    def test_hashline_formatting(self):
        filename1 = self.write_tamper_evident(b"Hello!", hashline=b"XXX {} YYY")

        with open(filename1, "rb") as f:
            self.assertEqual(f.read(), b"Hello!\nXXX a8d191538209e335154750d2df575b9ddfb16fc7 YYY\n")

    def test_validating_a_good_file(self):
        filename = self.write_tamper_evident(b"Am I OK?")
        tef = TamperEvidentFile(filename)
        self.assertTrue(tef.validate())

    def test_appending_is_detected(self):
        filename = self.write_tamper_evident(b"Am I OK?")

        with open(filename, "ab") as f:
            f.write(b"tamper\n")

        tef = TamperEvidentFile(filename)
        self.assertFalse(tef.validate())

    def test_editing_is_detected(self):
        filename = self.write_tamper_evident(b"Line 1\nLine 2\nLine 3\n")
        with open(filename, "rb") as f:
            text = f.read()
        with open(filename, "wb") as f:
            f.write(b"X")
            f.write(text[1:])
        tef = TamperEvidentFile(filename)
        self.assertFalse(tef.validate())

    def test_oneline_file_is_detected(self):
        filename = self.write_tamper_evident(b"Am I OK?")

        with open(filename, "wb") as f:
            f.write(b"tamper")

        tef = TamperEvidentFile(filename)
        self.assertFalse(tef.validate())
