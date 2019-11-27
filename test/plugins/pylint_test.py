"""Infrastructure for testing pylint plugins."""

import re
import textwrap
import warnings

from pylint.__pkginfo__ import numversion as pylint_numversion
from pylint.lint import Run
from pylint.reporters import CollectingReporter


def find_line_markers(source):
    """Find line markers in program source.

    Returns a dict mapping line numbers to the marker on that line.
    """
    markers = {}
    for lineno, line in enumerate(source.splitlines(), start=1):
        m = re.search(r"#=(\w+)", line)
        if m:
            markers[lineno] = m.group(1)
    return markers


def test_find_line_markers():
    markers = find_line_markers(
        """\
        line 1      #=A
        line 2
        line 3      #=Hello
        """
    )
    assert markers == {1: "A", 3: "Hello"}


class SimpleReporter(CollectingReporter):
    """A pylint message reporter that collects the messages in a list."""

    # Pylint does not specify well what a reporter must do.  This works.

    def _display(self, layout):
        pass


def run_pylint(source, msg_ids):
    """Run pylint on some source, collecting specific messages.

    `source` is the literal text of the program to check. It is
    dedented and written to a temp file for pylint to read.

    `msg_ids` is a comma-separated string of msgids we are interested
    in.  Use "all" to enable all messages.

    Returns a set of messages.  Each message is a string, formatted
    as "line:msg-id:message".  "line" will be the line number of the
    message, or if the source line has a comment like "#=Slug", then
    it will be "Slug" instead.  This makes it easier to write, read,
    and maintain the tests.

    """
    with open("source.py", "w") as f:
        f.write(textwrap.dedent(source))

    reporter = SimpleReporter()

    pylint_args = ["source.py", "--disable=all", "--enable={}".format(msg_ids)]
    if pylint_numversion >= (2, 0):
        kwargs = dict(do_exit=False)
    else:
        kwargs = dict(exit=False)

    Run(pylint_args, reporter=reporter, **kwargs)

    markers = find_line_markers(source)
    messages = {"{line}:{m.symbol}:{m.msg}".format(m=m, line=markers.get(m.line, m.line)) for m in reporter.messages}
    return messages


def test_that_we_can_test_pylint():
    # This tests that our pylint-testing function works properly.
    source = """\
        # There's no docstring, but we don't ask for that msgid,
        # so we won't get the warning.

        # Unused imports. We'll get warned about the first one,
        # but the second is disabled.
        import colorsys                 #=A
        import collections              # pylint: disable=unused-import

        # Three warnings on the same line, two different messages.
        # redefined-builtin is checked by an IAstroidChecker.
        # anomalous-backslash-in-string is checked by an ITokenChecker.
        int = float = "\\a\\b\\c"       #=B

        # TODO is checked by an IRawChecker. #=C
        """
    msg_ids = "unused-import,redefined-builtin,anomalous-backslash-in-string,fixme"
    with warnings.catch_warnings():
        # We want pylint to find the bad \c escape, but we don't want Python to warn about it.
        warnings.filterwarnings(action="ignore", category=DeprecationWarning, message="invalid escape")
        messages = run_pylint(source, msg_ids)
    expected = {
        "A:unused-import:Unused import colorsys",
        "B:redefined-builtin:Redefining built-in 'int'",
        "B:redefined-builtin:Redefining built-in 'float'",
        "B:anomalous-backslash-in-string:Anomalous backslash in string: '\\c'. "
        "String constant might be missing an r prefix.",
        "C:fixme:TODO is checked by an IRawChecker. #=C",
    }
    assert expected == messages


def test_invalid_python():
    source = """\
        This isn't even Python, what will pylint do?
        """
    messages = run_pylint(source, "all")
    assert len(messages) == 1
    message = messages.pop()
    # Pylint 1.x says the source is <string>, Pylint 2.x says <unknown>
    message = message.replace("<string>", "XXX").replace("<unknown>", "XXX")
    assert message == "1:syntax-error:invalid syntax (XXX, line 1)"


# I would have tested that the msgids must be valid, but pylint doesn't seem
# to mind being told to enable non-existent msgids.
