"""
Test ignore-long-lines regex
"""

from .pylint_test import run_pylint


def test_ignore_long_lines():
    source = """\
        # Bad
        a = 1  # hello world hello world hello world hello world hello world hello world hello world hello world hello world hello world
        # ..pii: hello world hello world hello world hello world hello world hello world hello world hello world hello world hello world
        '''
        < https://www.test.com/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world>
        hello world hello world hello world hello world hello world hello world hello world hello world hello world hello world hello world
        '''

        # Good
        '''
        .. pii: hello world hello world hello world hello world hello world hello world hello world hello world hello world hello world
        '''
        # .. pii: hello world hello world hello world hello world hello world hello world hello world hello world hello world hello world
        '''
        <https://www.test.com/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world>
        https://www.test.com/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world
        '''
        # <https://www.test.com/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world>
        # https://www.test.com/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world/hello/world
        # .. toggle_description: this is a good toggle, it goes back and forth, toggling a lot, which is what we expect toggles to do.
    """
    msg_ids = "line-too-long"
    messages = run_pylint(source, msg_ids)

    # normalize the messages by stripping off the 3rd segment.
    messages = {":".join(message.split(":")[:2]) for message in messages}

    expected = {"2:line-too-long", "3:line-too-long", "5:line-too-long", "6:line-too-long"}
    assert expected == messages
