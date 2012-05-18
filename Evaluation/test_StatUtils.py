# encoding=utf-8
import unittest

import math
import sympy
import sympy.physics.units as units

import Table
import StatUtils

class Mean(unittest.TestCase):
    def test_units(self):
        data = [x*units.m for x in (0.1, 0.2, 0.3)]
        symbol = sympy.Symbol("x")
        column = Table.MeasurementColumn(
            symbol,
            ("m", units.meter),
            data
        )
        mean, dev = StatUtils.mean(column.data)
        self.assertEqual(mean, 0.2)
        self.assertEqual(dev, math.sqrt(((0.1**2+0.2**2+0.3**2)/3 - 0.2**2) / 2))
        
