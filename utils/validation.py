import re
import typing.re


class regex:
    class partial:
        base64 = '[A-Za-z0-9+/=]'
        urlb64 = '[A-Za-z0-9-_]'
        basics = '[A-Za-z0-9 ]'

    class complete:
        base64 = re.compile('^[A-Za-z0-9+/]+={0,2}$')
        lowdot = re.compile('^[a-z]+([.][a-z]+)*$')
        kebabs = re.compile('^[A-Za-z](-?[A-Za-z0-9]+)*$')
        snakes = re.compile('^(_?[A-Za-z0-9]+)+$')


def validate_string(string: str, label: str, regex: typing.re.Pattern = None, min_len: int = 1, max_len: int = None):
    try:
        if not isinstance(label, str):
            raise Exception("Validation label must be a string.")

        if not isinstance(string, str):
            raise Exception("Must be a string.")

        if min_len is not None:
            if not isinstance(min_len, int):
                raise Exception("Minimum length must be an integer.")
            if len(string) < min_len:
                raise Exception(
                    "Must be at least %d characters long." % min_len)
        if max_len is not None:
            if not isinstance(max_len, int):
                raise Exception("Maximum length must be an integer.")
            if len(string) > max_len:
                raise Exception(
                    "Must be no more than %d characters long." % max_len)

        if regex is not None:
            if not isinstance(regex, typing.re.Pattern):
                raise Exception(
                    "Validation pattern must be a compiled RegEx pattern.")
            if not regex.match(string):
                raise Exception("Must match pattern '%s'." % regex.pattern)
    except Exception as e:
        raise Exception(
            "Failed to validate string for %s: %s" % (label, e)) from None
