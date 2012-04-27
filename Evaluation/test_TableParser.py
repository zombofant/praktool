# encoding=utf-8
from __future__ import unicode_literals, division, print_function

import unittest

import sympy
import sympy.physics.units

import Evaluation.TableParser as tp

class ParseCSV(unittest.TestCase):
    def setUp(self):
        pass

class ParseGnuplot(unittest.TestCase):
    def setUp(self):
        self.cols = tp.ParseGnuplot(b"""
# This is a comment, next line is an annotation
#% x/m*m t/s
1.0 1.0
4.0 2.0


# another comment
7.0 3.0
""".split(b'\n'))

    def test_cols(self):
        self.assertEqual(len(self.cols), 2)
        self.assertEqual(self.cols[0].symbol, sympy.Symbol(b'x'))
        self.assertEqual(self.cols[0].unitExpr, sympy.physics.units.m ** 2)
        self.assertEqual(self.cols[1].symbol, sympy.Symbol(b't'))
        self.assertEqual(self.cols[1].unitExpr, sympy.physics.units.s)

    def test_rows(self):
        m = sympy.physics.units.m
        m2 = m ** 2
        s = sympy.physics.units.s

        self.assertEqual(self.cols[0].data, [1.0, 4.0, 7.0])
        self.assertEqual(self.cols[1].data, [1.0, 2.0, 3.0])
