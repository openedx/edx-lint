""" Tests for the command line executable. """
import os
import unittest

from edx_lint.cmd import main


class WriteCommandTest(unittest.TestCase):
    """ Tests for the write command. """

    def call_command(self, argv=None):
        """ Call an edx_lint script command.

        Arguments:
            argv (list) -- arguments to pass to the edx_lint script
        """
        return main.main(argv)

    @unittest.skip('Default test runners have issues finding the file.')
    def test_pylintrc_file_created(self):
        """ Verify the command writes a pylintrc file. """
        filename = 'pylintrc'
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

        # Ensure the file does not already exist.
        if os.path.isfile(filepath):
            os.remove(filepath)

        self.assertEqual(0, self.call_command(['write', filename]))
        self.assertTrue(os.path.isfile(filepath))

        # Cleanup after ourselves
        os.remove(filepath)
