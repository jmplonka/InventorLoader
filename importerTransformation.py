# -*- coding: utf-8 -*-

'''
importerTransformation.py:
Importer for the Document's components
Simple approach to read/analyse Autodesk (R) Invetor (R) part file's (IPT) browser view data.
The importer can read files from Autodesk (R) Invetor (R) Inventro V2010 on. Older versions will fail!
TODO:
'''
from importerUtils import getFloat64, getUInt32, getUInt16, FloatArr2Str, logError
from FreeCAD         import Rotation as ROT, Vector as VEC, Matrix as MAT
import math

__author__     = 'Jens M. Plonka'
__copyright__  = 'Copyright 2018, Germany'
__url__        = "https://www.github.com/jmplonka/InventorLoader"

class Transformation:
	def __init__(self):
		self.a0 = 0x00000000
		self.a1 = []

	def read(self, data, offset):
		n, k = getUInt32(data, offset)
		if (n == 0x00000203):
			i = k
		else:
			i = offset
		#             +---- Value for the 4. row to be used for the transformation matrix
		#             |+--- Value for the 3. row to be used for the transformation matrix
		#             ||+-- Value for the 2. row to be used for the transformation matrix
		#             |||+- Value for the 1. row to be used for the transformation matrix
		#             ||||
		#             vvvv
		d1, i = getUInt16(data, i)
		#             +-------- Mask for the 4. row of the transformation matrix
		#             |+------- Mask for the 3. row of the transformation matrix
		#             ||+------ Mask for the 2. row of the transformation matrix
		#             |||+----- Mask for the 1. row of the transformation matrix
		#             ||||
		#             vvvv
		d2, i = getUInt16(data, i)
		self.a0 = d1 | (d2 << 16)
		n = 16 - bin(d1 | d2).count('1')
		self.m = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
		j = 0
		r = 0
		c = 0
		v = self.m[0]
		while (j < 16):
			b = (1 << j)
			if (d2 & b == 0):
				if (d1 & b == 0):
					v[c], i = getFloat64(data, i)
					if (math.fabs(v[c]) < 0.00001): v[c] = 0.0
				else:
					v[c] = 1
			else:
				if (d1 & b == 0):
					v[c] = 0
				else:
					v[c] = -1

			j += 1
			if ((j % 4) == 0):
				c = 0
				r += 1
				if (r < 4):
					v = self.m[r]
			else:
				c += 1
		return i

	def getX(self):
		return self.m[0][3] * 10.0

	def getY(self):
		return self.m[1][3] * 10.0

	def getZ(self):
		return self.m[2][3] * 10.0

	def __str__(self): # return unicode
		v = self.m[0]
		m1 = '[%s, %s, %s, %s]' %(v[0], v[1], v[2], v[3] * 10.0)
		v = self.m[1]
		m2 = '[%s, %s, %s, %s]' %(v[0], v[1], v[2], v[3] * 10.0)
		v = self.m[2]
		m3 = '[%s, %s, %s, %s]' %(v[0], v[1], v[2], v[3] * 10.0)
		v = self.m[3]
		m4 = '[%s, %s, %s, %s]' %(v[0], v[1], v[2], v[3] * 10.0)
		m = '[%s, %s, %s, %s]' %(m1, m2, m3, m4)
		j = 0
		mask = '|'
		d1 = (self.a0 & 0xFFFF0000) >> 16
		d2 = (self.a0 & 0x0000FFFF)
		while (j < 16):
			b = (1 << j)
			if (d1 & b):
				if (d2 & b):
					mask += '-'
				else:
					mask += '0'
			else:
				if (d2 & b):
					mask += '+'
				else:
					mask += 'x'
			j += 1
			if ((j % 4) == 0):
				mask += '|'
		return u' transformation={a0=%s m=[%s]}' %(mask, m)

	def getBase(self):
		x = self.m[0, 3]
		y = self.m[1, 3]
		z = self.m[2, 3]
		return VEC(x, y, z)

	def getRotation(self):
		"""Return quaternion from the transformation matrix.
		"""
		# the trace is the sum of the diagonal elements; see http://mathworld.wolfram.com/MatrixTrace.html
		xx = self.m[0][0]
		xy = self.m[0][1]
		xz = self.m[0][2]
		yx = self.m[1][0]
		yy = self.m[1][1]
		yz = self.m[1][2]
		zx = self.m[2][0]
		zy = self.m[2][1]
		zz = self.m[2][2]
		t = xx + yy + zz

		# we protect the division by s by ensuring that s>=1
		if (t >= 0): # |w| >= .5
			s = math.sqrt(t + 1) # |s|>=1 ...
			w = 0.5 * s
			s = 0.5 / s # so this division isn't bad
			x = (zy - yz) * s
			y = (xz - zx) * s
			z = (yx - xy) * s
		elif ((xx > yy) and (xx > zz)):
			s = math.sqrt(1.0 + xx - yy - zz) # |s|>=1
			x = s * 0.5 #|x| >= 0.5
			s = 0.5 / s
			y = (yx + xy) * s
			z = (xz + zx) * s
			w = (zy - yz) * s
		elif (yy > zz):
			s = math.sqrt(1.0 - xx + yy - zz) # |s|>=1
			y = s * 0.5 # |y| >= 0.5
			s = 0.5 / s
			x = (yx + xy) * s
			z = (zy + yz) * s
			w = (xz - zx) * s
		else:
			s = math.sqrt(1.0 + zz - xx - yy) # |s|>=1
			z = s * 0.5 # |z| >= 0.5
			s = 0.5 / s
			x = (xz + zx) * s
			y = (zy + yz) * s
			w = (yx - xy) * s
		return ROT(x, y, z, w)

	def getMatrix(self):
		m = self.m
		return MAT(
			m[0][0], m[0][1], m[0][2], m[0][3],
			m[1][0], m[1][1], m[1][2], m[1][3],
			m[2][0], m[2][1], m[2][2], m[2][3],
			m[3][0], m[3][1], m[3][2], m[3][3]
			)
