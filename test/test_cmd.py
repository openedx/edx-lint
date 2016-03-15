""" Tests for the command line executable. """

import os
import shutil
import tempfile
import unittest

from edx_lint.cmd import main


class WriteCommandTest(unittest.TestCase):
    """ Tests for the write command. """

    def setUp(self):
        super(WriteCommandTest, self).setUp()

        # Make a temporary directory to work in, and rm-rf it when we're done.
        tempdir = tempfile.mkdtemp(suffix="_edx_lint_test")
        self.addCleanup(shutil.rmtree, tempdir)

        # Change into the temp directory, and change back when we are done.
        thisdir = os.getcwd()
        self.addCleanup(os.chdir, thisdir)
        os.chdir(tempdir)

    def call_command(self, argv=None):
        """ Call an edx_lint script command.

        Arguments:
            argv (list) -- arguments to pass to the edx_lint script
        """
        return main.main(argv)

    def test_pylintrc_file_created(self):
        """ Verify the command writes a pylintrc file. """
        filename = 'pylintrc'

        # Assure the file does not already exist.
        self.assertFalse(os.path.isfile(filename))

        self.assertEqual(0, self.call_command(['write', filename]))
        self.assertTrue(os.path.isfile(filename))
