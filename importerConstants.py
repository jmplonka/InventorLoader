# -*- coding: utf-8 -*-

from FreeCAD import Vector as VEC
from math    import pi

REF_CROSS    = 1
REF_CHILD    = 2
REF_PARENT   = 3

VAL_GUESS    = 0
VAL_UINT8    = 1
VAL_UINT16   = 2
VAL_UINT32   = 3
VAL_UINT64   = 4
VAL_REF      = 5
VAL_STR8     = 6
VAL_STR16    = 7
VAL_DATETIME = 8
VAL_ENUM     = 9

VAL_FORMAT = {
	VAL_GUESS   : '%s',
	VAL_UINT8   : '%02X',
	VAL_UINT16  : '%03X',
	VAL_UINT32  : '%04X',
	VAL_UINT64  : '%05X',
	VAL_STR8    : '\'%s\'',
	VAL_STR16   : '\"%s\"',
	VAL_DATETIME: '#%s#',
	VAL_ENUM    : '%s',
}

MIN_0   = 0.0
MIN_PI  = -pi
MIN_PI2 = -pi / 2
MIN_INF = float('-inf')

MAX_2PI = 2 * pi
MAX_PI  = pi
MAX_PI2 = pi / 2
MAX_INF = float('inf')
MAX_LEN = 2e+100

CENTER = VEC(0, 0, 0)
DIR_X  = VEC(1, 0, 0)
DIR_Y  = VEC(0, 1, 0)
DIR_Z  = VEC(0, 0, 1)

ENCODING_FS      = 'utf8'
