"""
Commandline scripts to give one-time amnesty for specify linting error conditions.
"""



import logging
import re
import sys
from collections import namedtuple, defaultdict

import click
import click_log

LOG = logging.getLogger(__name__)
PYLINT_PARSEABLE_REGEX = re.compile(
    r"""^(?P<filename>[^:]+):(?P<linenum>\d+): """
    r"""\[(?P<error_code>[^(]+)\((?P<error_name>[^)]+)\), (?P<function>[^\]]*)\] """
    r"""(?P<error_msg>.*)"""
)
PYLINT_EXCEPTION_REGEX = re.compile(r"""\s*#\s*pylint:\s+disable=(?P<disables>[^#$]+?)(?=\s*(#|$))""")

PylintError = namedtuple("PylintError", ["filename", "linenum", "error_code", "error_name", "function", "error_msg"])


def parse_pylint_output(pylint_output):
    """
    Parse the pylint output-format=parseable lines into PylintError tuples.
    """
    for line in pylint_output:
        if not line.strip():
            continue

        if line[0:5] in ("-" * 5, "*" * 5):
            continue

        parsed = PYLINT_PARSEABLE_REGEX.search(line)
        if parsed is None:
            LOG.warning(
                "Unable to parse %r. If this is a lint failure, please re-run pylint with the "
                "--output-format=parseable option, otherwise, you can ignore this message.",
                line,
            )
            continue

        parsed_dict = parsed.groupdict()
        parsed_dict["linenum"] = int(parsed_dict["linenum"])
        yield PylintError(**parsed_dict)


def format_pylint_disables(error_names, tag=True):
    """
    Format a list of error_names into a 'pylint: disable=' line.
    """
    tag_str = "lint-amnesty, " if tag else ""
    if error_names:
        return "  # {tag}pylint: disable={disabled}".format(disabled=", ".join(sorted(error_names)), tag=tag_str)
    else:
        return ""


def fix_pylint(line, errors):
    """
    Yield any modified versions of ``line`` needed to address the errors in ``errors``.
    """
    if not errors:
        yield line
        return

    current = PYLINT_EXCEPTION_REGEX.search(line)
    if current:
        original_errors = {disable.strip() for disable in current.group("disables").split(",")}
    else:
        original_errors = set()

    disabled_errors = set(original_errors)

    for error in errors:
        if error.error_name == "useless-suppression":
            parsed = re.search("""Useless suppression of '(?P<error_name>[^']+)'""", error.error_msg)
            disabled_errors.discard(parsed.group("error_name"))
        elif error.error_name == "missing-docstring" and error.error_msg == "Missing module docstring":
            yield format_pylint_disables({error.error_name}).strip() + "\n"
        else:
            disabled_errors.add(error.error_name)

    disable_string = format_pylint_disables(disabled_errors, not disabled_errors <= original_errors)

    if current:
        yield PYLINT_EXCEPTION_REGEX.sub(disable_string, line)
    else:
        yield re.sub(r"($\s*)", disable_string + r"\1", line, count=1)


@click.command()
@click.option(
    "--pylint-output",
    default=sys.stdin,
    type=click.File(),
    help="An input file containing pylint --output-format=parseable errors. Defaults to stdin.",
)
@click_log.simple_verbosity_option(default="INFO")
def pylint_amnesty(pylint_output):
    """
    Add ``# pylint: disable`` clauses to add exceptions to all existing pylint errors in a codebase.
    """
    errors = defaultdict(lambda: defaultdict(set))
    for pylint_error in parse_pylint_output(pylint_output):
        errors[pylint_error.filename][pylint_error.linenum].add(pylint_error)

    for file_with_errors in sorted(errors):
        try:
            opened_file = open(file_with_errors)
        except OSError:
            LOG.warning("Unable to open %s for edits", file_with_errors, exc_info=True)
        else:
            with opened_file as input_file:
                output_lines = []
                for line_num, line in enumerate(input_file, start=1):
                    # If the line ends with backslash, take the amnesty to next line because line of code has not ended
                    if line.endswith('\\\n'):
                        errors[file_with_errors][line_num + 1] = errors[file_with_errors][line_num]
                        errors[file_with_errors][line_num] = set()

                    output_lines.extend(fix_pylint(line, errors[file_with_errors][line_num]))

            with open(file_with_errors, "w") as output_file:
                output_file.writelines(output_lines)
