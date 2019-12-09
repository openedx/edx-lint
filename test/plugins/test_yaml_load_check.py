"""Test yaml_load_check.py"""

from .pylint_test import run_pylint


MSG_IDS = "unsafe-yaml-load"


def test_unsafe_yaml_load_warnings():
    source = """\
        yaml.load('foo.bar')                      #=A
        yaml.load_all('foo.bar')                  #=B

    """
    messages = run_pylint(source, MSG_IDS)

    expected_messages = {
        "A:unsafe-yaml-load:yaml.load() call is unsafe, use yaml.safe_load()",
        "B:unsafe-yaml-load:yaml.load_all() call is unsafe, use yaml.safe_load_all()",
    }
    assert expected_messages == messages


def test_safe_yaml_invocations_are_fine():
    source = """\
        yaml.safe_load('this.is.fine')
        yaml.safe_load_all('this.is.fine')
        myaml.load('this.is.fine.too')
        myaml.load_all('this.is.fine.too')

    """
    messages = run_pylint(source, MSG_IDS)
    assert not messages
