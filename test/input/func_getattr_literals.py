"""These are bad uses of getattr() and setattr()"""

# pylint: disable=missing-docstring

def do_things(name):
    hello = getattr(name, "hello")
    world = getattr(name, "hello", 17)
    setattr(name, "hello", hello)
    setattr(name, "h" + "ello", world)
    delattr(name, "something")
    delattr(name, "FOO".lower())

    # the message can be disabled:
    hello = getattr(name, "hello")      # pylint: disable=literal-used-as-attribute

    # Account for this case in our code...
    world = getattr(name, 1)
