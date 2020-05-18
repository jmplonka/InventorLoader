# dxfgrabber - copyright (C) 2012 by Manfred Moitzi (mozman)
# Purpose: grab information from DXF drawings - all DXF versions supported
# Created: 21.07.2012
# License: MIT License

version = (1, 0, 0)
VERSION = "%d.%d.%d" % version

__author__ = "mozman <mozman@gmx.at>"
__doc__ = """A Python library to grab information from DXF drawings - all DXF versions supported."""

import sys, io

PYTHON3 = sys.version_info.major > 2

# if tostr does not work, look at package 'dxfwrite' for escaping unicode chars
if PYTHON3:
    tostr = str
else:  # PYTHON27
    tostr = unicode

from .tags import dxfinfo
from .drawing import Drawing

def get_encoding(filename):
    with io.open(filename) as fp:
        info = dxfinfo(fp)
    return info.encoding

def _read_encoded_file(filename, options, encoding='utf-8', errors='strict'):
    with io.open(filename, encoding=encoding, errors=errors) as fp:
        dwg = Drawing(fp, options)
    dwg.filename = filename
    return dwg

def readfile(filename, options=None):
    try:  # is it ascii code-page encoded?
        return _read_encoded_file(filename, options, encoding=get_encoding(filename), errors='strict')
    except UnicodeDecodeError:  # try unicode and ignore errors
        return _read_encoded_file(filename, options, encoding='utf-8', errors='ignore')
