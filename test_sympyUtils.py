# encoding=utf-8
import unittest

import sympy
import sympy.physics.units as units

import sympyUtils

class iterSymbols(unittest.TestCase):
    def test_simple(self):
        x, y, z, w = sympy.symbols("x y z w")
        d = sympy.Dummy("d")
        expr = x**d + y*z - w
        self.assertEqual(set(sympyUtils.iterSymbols(expr)), set((x, y, z, w, d)))
