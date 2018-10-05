import re


def pathify(label):
    """
      Convert a label into something that can be used in a URI path segment.
    """
    return re.sub('-\$', '',
                  re.sub('-+', '-',
                         re.sub('[^\\w/]', '-', label.lower())))


def is_interactive():
    import __main__ as main
    return not hasattr(main, '__file__')