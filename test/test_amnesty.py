"""
Tests of the lint-amnesty command.
"""

from collections import defaultdict
from io import StringIO
import itertools
import textwrap
import unittest

from edx_lint.cmd.amnesty import PylintError, fix_pylint, PYLINT_EXCEPTION_REGEX, parse_pylint_output


class AmnestyTest(unittest.TestCase):
    """
    Tests of lint-amnesty.
    """

    def assert_amnesty(self, input_code, errors, expected):
        """
        Assert that fix_pylint produces ``expected`` when fed ``input_code`` and the
        list of errors ``errors``.

        Arguments:
            input_code: A string of python code. Will be textwrap.dedented.
            errors: A list of PylintErrors
            expected: A string of python code. Will be textwrap.dedented.
        """
        input_code = textwrap.dedent(input_code)
        expected = textwrap.dedent(expected)

        errors_by_line = defaultdict(list)
        for error in errors:
            errors_by_line[error.linenum].append(error)

        output_lines = itertools.chain.from_iterable(
            fix_pylint(line, errors_by_line[lineno]) for lineno, line in enumerate(StringIO(input_code), start=1)
        )

        self.assertEqual(expected.split(u"\n"), "".join(output_lines).split(u"\n"))

    def assert_pylint_exception_match(self, expected, line):
        """
        Assert that PYLINT_EXCEPTION_REGEX mateches ``expected`` in ``line``.
        """
        self.assertEqual(expected, PYLINT_EXCEPTION_REGEX.search(line).group(0))

    def test_pylint_exception_re(self):
        self.assert_pylint_exception_match(
            "  # pylint: disable=some-exception, other-exception",
            "some line  # pylint: disable=some-exception, other-exception",
        )
        self.assert_pylint_exception_match(
            "  # pylint: disable=some-exception,other-exception",
            "some line  # pylint: disable=some-exception,other-exception",
        )
        self.assert_pylint_exception_match(
            "  # pylint: disable=some-exception", "some line  # pylint: disable=some-exception"
        )
        self.assert_pylint_exception_match(
            "  # pylint: disable=some-exception", "some line  # pylint: disable=some-exception#noqa"
        )
        self.assert_pylint_exception_match(
            "  # pylint: disable=some-exception", "some line  # pylint: disable=some-exception  #noqa"
        )
        self.assert_pylint_exception_match(
            "# pylint: disable=some-exception", "some line# pylint: disable=some-exception#noqa"
        )

    def test_parse_pylint_output(self):
        pylint_output = textwrap.dedent(
            '''\
            ************* Module cms.urls
            cms/urls.py:1: [C0111(missing-docstring), ] Missing module docstring
            ************* Module cms.envs.test
            cms/envs/test.py:81: [C0301(line-too-long), ] Line too long (144/120)
            ************* Module test.test_amnesty
            test/test_amnesty.py:78: [C0326(bad-whitespace), ] Exactly one space required around assignment
                    pylint_output=textwrap.dedent("""\\
                                 ^
        '''
        )
        self.assertEqual(
            [
                PylintError("cms/urls.py", 1, "C0111", "missing-docstring", "", "Missing module docstring"),
                PylintError("cms/envs/test.py", 81, "C0301", "line-too-long", "", "Line too long (144/120)"),
                PylintError(
                    "test/test_amnesty.py",
                    78,
                    "C0326",
                    "bad-whitespace",
                    "",
                    "Exactly one space required around assignment",
                ),
            ],
            list(parse_pylint_output(pylint_output.split("\n"))),
        )

    def test_add_supression(self):
        input_code = u"""\
            def func(arg):
                pass
        """

        errors = [PylintError("test.py", 1, "W0613", "unused-argument", "func", "Unused argument 'arg'")]

        expected = u"""\
            def func(arg):  # lint-amnesty, pylint: disable=unused-argument
                pass
        """

        self.assert_amnesty(input_code, errors, expected)

    def test_add_multiple_suppressions_same_line(self):
        input_code = u"""\
            def func(arg, arg):
                pass
        """

        errors = [
            PylintError("test.py", 1, "W0613", "unused-argument", "func", "Unused argument 'arg'"),
            PylintError("test.py", 1, "E0108", "duplicate-argument-name", "func", "Duplicate argument name 'arg'"),
        ]

        expected = u"""\
            def func(arg, arg):  # lint-amnesty, pylint: disable=duplicate-argument-name, unused-argument
                pass
        """

        self.assert_amnesty(input_code, errors, expected)

    def test_add_to_existing_suppression(self):
        input_code = u"""\
            def func(arg, arg):  # pylint: disable=unused-argument
                pass
        """

        errors = [
            PylintError("test.py", 1, "E0108", "duplicate-argument-name", "func", "Duplicate argument name 'arg'")
        ]

        expected = u"""\
            def func(arg, arg):  # lint-amnesty, pylint: disable=duplicate-argument-name, unused-argument
                pass
        """

        self.assert_amnesty(input_code, errors, expected)

    def test_add_to_existing_suppression_trailing_comment(self):
        input_code = u"""\
            def func(arg, arg):  # pylint: disable=unused-argument  # noqa
                pass
        """

        errors = [
            PylintError("test.py", 1, "E0108", "duplicate-argument-name", "func", "Duplicate argument name 'arg'")
        ]

        expected = u"""\
            def func(arg, arg):  # lint-amnesty, pylint: disable=duplicate-argument-name, unused-argument  # noqa
                pass
        """

        self.assert_amnesty(input_code, errors, expected)

    def test_add_suppression_trailing_comment(self):
        input_code = u"""\
            def func(arg, arg):  # noqa
                pass
        """

        errors = [
            PylintError("test.py", 1, "E0108", "duplicate-argument-name", "func", "Duplicate argument name 'arg'")
        ]

        expected = u"""\
            def func(arg, arg):  # noqa  # lint-amnesty, pylint: disable=duplicate-argument-name
                pass
        """

        self.assert_amnesty(input_code, errors, expected)

    def test_remove_useless_suppression(self):
        input_code = u"""\
            def func(arg, arg):  # pylint: disable=unused-argument
                pass
        """

        errors = [
            PylintError(
                "test.py", 1, "I0021", "useless-suppression", "func", "Useless suppression of 'unused-argument'"
            )
        ]

        expected = u"""\
            def func(arg, arg):
                pass
        """

        self.assert_amnesty(input_code, errors, expected)

    def test_remove_useless_suppression_leave_rest(self):
        input_code = u"""\
            def func(arg, arg):  # pylint: disable=unused-argument, duplicate-argument-name
                pass
        """

        errors = [
            PylintError(
                "test.py", 1, "I0021", "useless-suppression", "func", "Useless suppression of 'unused-argument'"
            )
        ]

        expected = u"""\
            def func(arg, arg):  # pylint: disable=duplicate-argument-name
                pass
        """

        self.assert_amnesty(input_code, errors, expected)

    def test_replace_useless_suppression(self):
        input_code = u"""\
            def func(arg, arg):  # pylint: disable=unused-argument
                pass
        """

        errors = [
            PylintError(
                "test.py", 1, "I0021", "useless-suppression", "func", "Useless suppression of 'unused-argument'"
            ),
            PylintError("test.py", 1, "E0108", "duplicate-argument-name", "func", "Duplicate argument name 'arg'"),
        ]

        expected = u"""\
            def func(arg, arg):  # lint-amnesty, pylint: disable=duplicate-argument-name
                pass
        """

        self.assert_amnesty(input_code, errors, expected)

    def test_fix_multiple_lines(self):
        input_code = u"""\
            def func_a(arg):
                pass

            def func_b(arg, arg):
                pass
        """

        errors = [
            PylintError("test.py", 1, "W0613", "unused-argument", "func", "Unused argument 'arg'"),
            PylintError("test.py", 4, "E0108", "duplicate-argument-name", "func", "Duplicate argument name 'arg'"),
        ]

        expected = u"""\
            def func_a(arg):  # lint-amnesty, pylint: disable=unused-argument
                pass

            def func_b(arg, arg):  # lint-amnesty, pylint: disable=duplicate-argument-name
                pass
        """

        self.assert_amnesty(input_code, errors, expected)

    def test_fix_module_docstring_missing(self):
        input_code = u"""\
            def func(arg):
                pass
        """

        errors = [PylintError("test.py", 1, "C0111", "missing-docstring", "func", "Missing module docstring")]

        expected = u"""\
            # lint-amnesty, pylint: disable=missing-docstring
            def func(arg):
                pass
        """

        self.assert_amnesty(input_code, errors, expected)

    def test_fix_module_and_func_docstring_missing(self):
        input_code = u"""\
            def func(arg):
                pass
        """

        errors = [
            PylintError("test.py", 1, "C0111", "missing-docstring", "func", "Missing module docstring"),
            PylintError("test.py", 1, "C0111", "missing-docstring", "func", "Missing function docstring"),
        ]

        expected = u"""\
            # lint-amnesty, pylint: disable=missing-docstring
            def func(arg):  # lint-amnesty, pylint: disable=missing-docstring
                pass
        """

        self.assert_amnesty(input_code, errors, expected)

    def test_fix_many_errors(self):
        input_code = u"""\
            def foo(self, arg, blarg, flarg, blanth, notehu, onethu, psonatehu):
                pass"""

        errors = [
            PylintError("lint_test.py", 2, "C0304", "missing-final-newline", "", "Final newline missing"),
            PylintError("lint_test.py", 1, "C0111", "missing-docstring", "", "Missing module docstring"),
            PylintError("lint_test.py", 1, "C0102", "blacklisted-name", "foo", 'Black listed name "foo"'),
            PylintError("lint_test.py", 1, "C0111", "missing-docstring", "foo", "Missing function docstring"),
            PylintError("lint_test.py", 1, "W0613", "unused-argument", "foo", "Unused argument 'notehu'"),
            PylintError("lint_test.py", 1, "W0613", "unused-argument", "foo", "Unused argument 'self'"),
            PylintError("lint_test.py", 1, "W0613", "unused-argument", "foo", "Unused argument 'psonatehu'"),
            PylintError("lint_test.py", 1, "W0613", "unused-argument", "foo", "Unused argument 'blanth'"),
            PylintError("lint_test.py", 1, "W0613", "unused-argument", "foo", "Unused argument 'onethu'"),
            PylintError("lint_test.py", 1, "W0613", "unused-argument", "foo", "Unused argument 'arg'"),
            PylintError("lint_test.py", 1, "W0613", "unused-argument", "foo", "Unused argument 'blarg'"),
            PylintError("lint_test.py", 1, "W0613", "unused-argument", "foo", "Unused argument 'flarg'"),
        ]

        expected = u"""\
            # lint-amnesty, pylint: disable=missing-docstring
            def foo(self, arg, blarg, flarg, blanth, notehu, onethu, psonatehu):  # lint-amnesty, pylint: disable=blacklisted-name, missing-docstring, unused-argument
                pass  # lint-amnesty, pylint: disable=missing-final-newline"""

        self.assert_amnesty(input_code, errors, expected)
