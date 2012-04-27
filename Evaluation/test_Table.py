# encoding=utf-8
import unittest

import sympy
import sympy.physics.units as units

import Table

class DataTest(unittest.TestCase):
    def setUp(self):
        self.symbol = sympy.Symbol("x")
        self.data = [value*units.mile for value in xrange(10)]
        self.unit = units.meter
    
class DataColumn(DataTest):
    def setUp(self):
        super(DataColumn, self).setUp()
        self.col = Table.DataColumn(self.symbol, ("m", self.unit), self.data,
            defaultMagnitude=1)
        self.displayData = [value/self.unit for value in self.data]
        self.displayList = [(value, unicode(self.unit)) for value in self.displayData]

    def test_init(self):
        self.assertEqual(list(self.col), self.displayData)

    def test_display(self):
        self.assertEqual(list(self.col.iterDisplay()), self.displayList)

    def tearDown(self):
        del self.col

class DerivatedColumn(DataTest):
    def setUp(self):
        super(DerivatedColumn, self).setUp()
        self.unit = units.meter**3
        self.data = [value*(units.mile**3) for value in range(10)]
        self.dataSymbol = sympy.Symbol("r")
        self.dataColumn = Table.DataColumn(self.dataSymbol, ("m³", self.unit),
            self.data, defaultMagnitude=1)
        self.derivColumn = Table.DerivatedColumn(self.symbol, ("kg", units.kilogram),
            [self.dataColumn], self.dataSymbol * (units.kilogram/(units.meter**3)),
            defaultMagnitude=1)

    def test_calc(self):
        calcData = [(value/self.unit, "kg") for value in self.data]
        self.assertEqual(list(self.derivColumn.iterDisplay()), calcData)
        del self.derivColumn
        
    def test_multi(self):
        self.dataSymbol2 = sympy.Symbol("s")
        self.dataColumn2 = Table.DataColumn(
            self.dataSymbol2,
            ("m/s^2", units.meter/(units.second**2)),
            [value*(units.mile/(units.hour**2)) for value in range(10)],
            defaultMagnitude=1
        )
        self.derivSymbol2 = sympy.Symbol("F")
        self.derivColumn2 = Table.DerivatedColumn(
            self.derivSymbol2,
            ("N", units.newton),
            [self.dataColumn2, self.derivColumn],
            self.symbol * self.dataSymbol2,
            defaultMagnitude=1
        )
        finalData = [(value*(units.mile**3)*(units.kilogram/(units.meter**3))*value*units.mile/(units.hour**2) / (units.newton)) for value in range(10)]
        self.assertEqual(list(self.derivColumn2), finalData)
