"""Test getattr_check.py"""

from .pylint_test import run_pylint


def test_getattr_checker():
    source = """\
        getattr(name, "hello")                  #=A
        getattr(name, "hello", 17)
        getattr(name, "hello", None)

        setattr(name, "hello", hello)           #=B
        setattr(name, "h" + "ello", world)

        delattr(name, "something")              #=C
        delattr(name, "FOO".lower())

        # You can use a literal if it's not a valid identifier
        getattr(name, "hello-world")
        getattr(name, "hello.world")
        getattr(name, "")
        getattr(name, " ")
        getattr(name, "1x")

        # The warnings can be disabled
        getattr(name, "_")                      # pylint: disable=literal-used-as-attribute
        if 1:
            # pylint: disable=literal-used-as-attribute
            getattr(name, "Hello")
            setattr(name, "hello", "hello")

        # More bad cases
        getattr(name, "hello1")                 #=D
        getattr(name, "_")                      #=E

        # Account for this case in our code...
        world = getattr(name, 1)

        # We don't get confused by another function nname
        foobar(name, "hello")
    """
    msg_ids = "literal-used-as-attribute"
    messages = run_pylint(source, msg_ids)
    expected = {
        "A:literal-used-as-attribute:getattr using a literal attribute name",
        "B:literal-used-as-attribute:setattr using a literal attribute name",
        "C:literal-used-as-attribute:delattr using a literal attribute name",
        "D:literal-used-as-attribute:getattr using a literal attribute name",
        "E:literal-used-as-attribute:getattr using a literal attribute name",
    }
    assert expected == messages
