"""Better os.path.expandvars."""
import os


class FakeEnviron:
    """Replacement for os.environ.

    returns empty strings if a variable does not exist.
    """

    def __init__(self):
        self._original = os.environ

    def __enter__(self):
        # Only replace os.envion if context manager is used
        os.environ = self
        return self

    def __exit__(self, *_):
        os.environ = self._original

    def __getitem__(self, item):
        try:
            return self._original[item]
        except KeyError:
            # If that variable does not exist, return empty
            return ""


def expandvars(string):
    """Expand shell variables of form $var and ${var}.

    Unknown variables become empty. Escapes allowed.
    """
    # Find a string that can be used to replace "\$"
    replacer = '\0'
    while replacer in string:
        # loop is guaranteed to exit as len(string) is finite
        replacer *= 2

    string = string.replace('\\$', replacer)

    with FakeEnviron():
        return os.path.expandvars(string).replace(replacer, '$')
