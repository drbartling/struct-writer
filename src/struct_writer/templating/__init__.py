import collections
import copy
import logging
import re
from collections import namedtuple
from typing import Any

_logger = logging.getLogger(__name__)
_sentinel_dict = {}


# pylint: disable=dangerous-default-value
# We use the fact that a default of a dict type is static in order to detect if
# the __mapping variable was not passed.
class Template:
    patter_str = r"\$(?:(?P<escaped>\$)|{(?P<braced>.+?)}|(?P<invalid>))"

    def __init__(self, template):
        self.pattern: re.Pattern = re.compile(self.patter_str, re.VERBOSE)
        self.template = template

    def render(self, __mapping=_sentinel_dict, /, **kwds) -> str:
        # Using the fact that a default dict is a fixed object to detect if an
        # unnamed mapping dictioanry was passed in.
        mapping = self._mapping(__mapping, **kwds)
        mapping = named_tuple_from_dict("mapping", mapping)

        def convert(match_object):
            # Explicitely use `mapping` in this closure, otherwise the implicite
            # use in eval won't work
            mapping  # pylint: disable=pointless-statement

            if expression := match_object.group("braced"):
                f_string = rf'f"{{mapping.{expression}}}"'
                try:
                    return eval(f_string)  # pylint: disable=eval-used
                except Exception:
                    _logger.error("Failed to evaluate %s", f_string)
                    raise
            if expression := match_object.group("escaped"):
                return "$"
            return match_object.group()

        result = None
        template = self.template
        while result != template:
            template = result or self.template
            result = self.pattern.sub(convert, template)

        return result

    def safe_render(self, __mapping=_sentinel_dict, /, **kwds) -> str:
        # Using the fact that a default dict is a fixed object to detect if an
        # unnamed mapping dictioanry was passed in.
        mapping = self._mapping(__mapping, **kwds)
        mapping = named_tuple_from_dict("mapping", mapping)

        def convert(match_object):
            # Explicitely use `mapping` in this closure, otherwise the implicite
            # use in eval won't work
            mapping  # pylint: disable=pointless-statement

            if expression := match_object.group("braced"):
                f_string = rf'f"{{mapping.{expression}}}"'
                try:
                    return eval(f_string)  # pylint: disable=eval-used
                except Exception:  # pylint: disable=broad-exception-caught
                    return match_object.group()
            if expression := match_object.group("escaped"):
                return "$"
            return match_object.group()

        result = None
        template = self.template
        while result != template:
            template = result or self.template
            result = self.pattern.sub(convert, template)

        return result

    def _mapping(self, __mapping=_sentinel_dict, /, **kwds) -> dict[str, Any]:
        assert isinstance(__mapping, dict)
        assert isinstance(kwds, dict)

        if __mapping is _sentinel_dict:
            mapping = kwds
        else:
            mapping = merge(__mapping, kwds)
        return mapping


def named_tuple_from_dict(name: str, dictionary: dict[str, Any]):
    assert isinstance(dictionary, collections.abc.MutableMapping)
    dictionary = copy.deepcopy(dictionary)

    for k, v in dictionary.items():
        if isinstance(v, collections.abc.MutableMapping):
            dictionary[k] = named_tuple_from_dict(k, v)

    new_tuple = namedtuple(name, dictionary)
    tuple_obj = new_tuple(**dictionary)
    return tuple_obj


def merge(a, b):  # pragma: no cover
    for k, vb in b.items():
        if va := a.get(k):
            if isinstance(vb, collections.abc.MutableMapping) and isinstance(
                va, collections.abc.MutableMapping
            ):
                merge(va, vb)
            else:
                a[k] = b[k]
        else:
            a[k] = b[k]
    return a
