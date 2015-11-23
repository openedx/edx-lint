"""These are bad uses of getattr() and setattr()"""

# pylint: disable=missing-docstring

def do_things(name):
    hello = getattr(name, "hello")
    world = getattr(name, "hello", 17)
    setattr(name, "hello", hello)
    setattr(name, "h" + "ello", world)
    delattr(name, "something")
    delattr(name, "FOO".lower())
