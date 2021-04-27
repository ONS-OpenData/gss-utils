
from gssutils.transform.writers.abstract import CubeWriter

class CMDWriter(CubeWriter):
    """
    An implementation of the CubeWriter abstract (i.e a "driver") that outputs data
    and metadata to satisfy the CMD platform
    """