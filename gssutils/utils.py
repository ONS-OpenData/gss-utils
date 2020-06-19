import re

from typing import Union, Sequence, Any, List
from unidecode import unidecode


def pathify(label):
    """
      Convert a label into something that can be used in a URI path segment.
    """
    return re.sub(r'-$', '',
                  re.sub(r'-+', '-',
                         re.sub(r'[^\w/]', '-', unidecode(label).lower())))


def is_interactive():
    import __main__ as main
    return not hasattr(main, '__file__')


def ensure_list(o: Any) -> List:
    if isinstance(o, List):
        return o
    else:
        return [o]
