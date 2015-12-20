"""Test main for edx-lint."""

import os
import unittest


def load_tests(unused_loader, tests, unused_pattern):
    """Loads tests for the pylint test loader.

    This function is automatically run by pylint's test runner, and is called
    with three arguments, two of which we don't need.

    """
    # Have to import this in the function, because the module does
    # initialization on import! ugh.
    from pylint.testutils import make_tests, LintTestUsingFile, cb_test_gen, linter

    # Load our plugin.
    linter.load_plugin_modules(['edx_lint.pylint'])

    here = os.path.dirname(os.path.abspath(__file__))

    tests = make_tests(
        input_dir=os.path.join(here, 'input'),
        msg_dir=os.path.join(here, 'messages'),
        filter_rgx=None,
        callbacks=[cb_test_gen(LintTestUsingFile)],
    )

    cls = unittest.TestSuite
    return cls(unittest.makeSuite(test, suiteClass=cls) for test in tests)
