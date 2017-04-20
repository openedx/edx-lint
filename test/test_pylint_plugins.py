"""Test main for edx-lint."""

import os
import unittest
import re

def load_tests(unused_loader, tests, unused_pattern):  # pylint: disable=unused-argument
    """Loads tests for the pylint test loader.

    This function is automatically run by pylint's test runner, and is called
    with three arguments, two of which we don't need.

    """
    # Have to import this in the function, because the module does
    # initialization on import! ugh.
    from pylint.testutils import LintTestUsingFile, linter, get_tests_info

    # Inline functions that was deleted from pylint core
    def cb_test_gen(base_class):
        """Inlined from pylint"""
        def call(input_dir, msg_dir, module_file, messages_file, dependencies):
            """Inlined from pylint"""
            class LintTC(base_class):
                """Inlined from pylint"""
                module = module_file.replace('.py', '')
                output = messages_file
                depends = dependencies or None
                INPUT_DIR = input_dir
                MSG_DIR = msg_dir
            return LintTC
        return call

    def make_tests(input_dir, msg_dir, filter_rgx, callbacks):
        """generate tests classes from test info

        return the list of generated test classes
        """
        if filter_rgx:
            is_to_run = re.compile(filter_rgx).search
        else:
            is_to_run = lambda x: 1
        tests = []
        for module_file, messages_file in (
                get_tests_info(input_dir, msg_dir, 'func_', '')
        ):
            if not is_to_run(module_file) or module_file.endswith(('.pyc', "$py.class")):
                continue
            base = module_file.replace('func_', '').replace('.py', '')

            dependencies = get_tests_info(input_dir, msg_dir, base, '.py')

            for callback in callbacks:
                test = callback(input_dir, msg_dir, module_file, messages_file,
                                dependencies)
                if test:
                    tests.append(test)
        return tests


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
