# encoding=utf-8
from __future__ import division, print_function
from our_future import *

import unittest

import sympy
import sympy.physics.units as units

import Column
import Table

class TableTest(unittest.TestCase):
    def setUp(self):
        table = Table.Table()
        self.table = table
        
        lengthSymbol = sympy.Symbol("x")
        lengthData = [value*units.m for value in range(10)]
        table.add(Column.MeasurementColumn(
            lengthSymbol,
            ("m", units.m),
            lengthData
        ))
        self.lengthSymbol, self.lengthData = lengthSymbol, lengthData
        
        timeSymbol = sympy.Symbol("t")
        timeData = [value*units.s for value in range(10)]
        table.add(Column.MeasurementColumn(
            timeSymbol,
            ("s", units.s),
            timeData
        ))
        self.timeSymbol, self.timeData = timeSymbol, timeData

        volumeSymbol = sympy.Symbol("V")
        volumeData = [value*units.m**3 for value in range(10)]
        table.add(Column.MeasurementColumn(
            volumeSymbol,
            ("m³", units.m**3),
            volumeData
        ))
        self.volumeSymbol, self.volumeData = volumeSymbol, volumeData
        
        massSymbol = sympy.Symbol("m")
        massData = [value*units.kg for value in range(1, 11)]
        table.add(Column.MeasurementColumn(
            massSymbol,
            ("kg", units.kg),
            massData
        ))
        self.massSymbol, self.massData = massSymbol, massData

    def test_derivate(self):
        density = sympy.Symbol("rho")
        V, m = self.volumeSymbol, self.massSymbol
        col = self.table.derivate(
            density,
            ("kg/cm³", units.kg / (units.cm**3)),
            m / V
        )
        col.update(True)
        self.assertEqual(list(col), [(sympy.sympify("{0}/({1}*10**6)".format(x, y)), {}) for y, x in zip(range(10), range(1, 11))])

    def test_unknownSymbol(self):
        foo, bar = sympy.Dummy("foo"), sympy.Dummy("bar")
        self.assertRaises(KeyError, self.table.derivate,
            foo,
            ("kg", units.kg),
            bar
        )

    def test_invalidUnit(self):
        density = sympy.Symbol("rho")
        V, m = self.volumeSymbol, self.massSymbol
        self.assertRaises(ValueError, self.table.derivate,
            density,
            ("kg", units.kg),
            m / V
        )

    def test_notIndependent(self):
        density = sympy.Symbol("rho")
        V, m = self.volumeSymbol, self.massSymbol
        self.assertRaises(ValueError, self.table.derivate,
            density,
            ("kg", units.kg),
            m / V
        )

    def test_diff(self):
        dx, dt, v = sympy.symbols("dx dt v")
        self.table.diff(self.lengthSymbol, dx)
        self.table.diff(self.timeSymbol, dt)
        velocity = self.table.derivate(
            v,
            ("m/s", units.m/units.s),
            dx / dt
        )
        velocity.update(True)
        self.assertEqual(list(velocity), [(1, {})] * 9)

    def tearDown(self):
        del self.table
        del self.lengthSymbol, self.lengthData
        del self.timeSymbol, self.timeData
        del self.volumeSymbol, self.volumeData
        del self.massSymbol, self.massData
