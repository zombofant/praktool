# encoding=utf-8
from __future__ import division, print_function
from our_future import *

import sympy
import sympy.physics.units as units

import unittest

import Column

class DataTest(unittest.TestCase):
    def setUp(self):
        self.symbol = sympy.Symbol("x")
        self.data = [value*units.mile for value in xrange(10)]
        self.unit = units.meter
    
class MeasurementColumn(DataTest):
    def setUp(self):
        super(MeasurementColumn, self).setUp()
        self.col = Column.MeasurementColumn(
            self.symbol,
            ("m", self.unit),
            self.data
        )
        self.displayData = [(value/self.unit, {}) for value in self.data]

    def test_init(self):
        self.assertEqual(len(self.col), len(self.data))
        self.assertEqual(list(self.col), self.displayData)

    def tearDown(self):
        del self.col

class DerivatedColumn(DataTest):
    def setUp(self):
        super(DerivatedColumn, self).setUp()
        self.unit = units.meter**3
        self.data = [value*(units.mile**3) for value in range(10)]
        self.dataSymbol = sympy.Symbol("r")
        self.dataColumn = Column.MeasurementColumn(
            self.dataSymbol,
            ("m³", self.unit),
            self.data
        )
        self.derivColumn = Column.DerivatedColumn(
            self.symbol,
            ("kg", units.kilogram),
            [self.dataColumn],
            self.dataSymbol * (units.kilogram/(units.meter**3))
        )

    def test_calc(self):
        calcData = [(value/self.unit, {}) for value in self.data]
        self.derivColumn.update(True)
        self.assertEqual(list(self.derivColumn), calcData)
        del self.derivColumn
        
    def test_multi(self):
        self.dataSymbol2 = sympy.Symbol("s")
        self.dataColumn2 = Column.MeasurementColumn(
            self.dataSymbol2,
            ("m/s^2", units.meter/(units.second**2)),
            [value*(units.mile/(units.hour**2)) for value in range(10)]
        )
        self.derivSymbol2 = sympy.Symbol("F")
        self.derivColumn2 = Column.DerivatedColumn(
            self.derivSymbol2,
            ("N", units.newton),
            [self.dataColumn2, self.derivColumn],
            self.symbol * self.dataSymbol2
        )
        self.derivColumn2.update(True)
        finalData = [(value*(units.mile**3)*(units.kilogram/(units.meter**3))*value*units.mile/(units.hour**2) / (units.newton), {}) for value in range(10)]
        self.assertEqual(list(self.derivColumn2), finalData)
