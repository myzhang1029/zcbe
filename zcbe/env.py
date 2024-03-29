"""Better os.path.expandvars."""
import os
from typing import Any


class FakeEnviron:
    """Replacement for os.environ.

    returns empty strings if a variable does not exist.
    """

    def __init__(self) -> None:
        self._original = os.environ

    def __enter__(self) -> "FakeEnviron":
        # Only replace os.envion if context manager is used
        os.environ = self  # type: ignore # intended to mock it
        return self

    def __exit__(self, *_: Any) -> None:
        os.environ = self._original

    def __getitem__(self, item: str) -> str:
        try:
            return self._original[item]
        except KeyError:
            # If that variable does not exist, return empty
            return ""


def expandvars(string_any: Any) -> str:
    """Expand shell variables of form $var and ${var}.

    Unknown variables become empty. Escapes allowed.
    """
    string = str(string_any)
    # Find a string that can be used to replace "\$"
    replacer = '\0'
    while replacer in string:
        # loop is guaranteed to exit as len(string) is finite
        replacer *= 2  # pragma: no cover

    string = string.replace('\\$', replacer)

    with FakeEnviron():
        return os.path.expandvars(string).replace(replacer, '$')
