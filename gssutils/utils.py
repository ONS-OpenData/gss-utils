import re


def pathify(label):
    """
      Convert a label into something that can be used in a URI path segment.
    """
    return re.sub('-\$', '',
                  re.sub('-+', '-',
                         re.sub('[^\\w/]', '-', label.lower())))