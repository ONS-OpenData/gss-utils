import re


def pathify(label):
    """
      Convert a label into something that can be used in a URI path segment.
    """
    return re.sub(r'-$', '',
                  re.sub(r'-+', '-',
                         re.sub(r'[^\w/]', '-', label.lower())))


def is_interactive():
    import __main__ as main
    return not hasattr(main, '__file__')
