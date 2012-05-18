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
    
class MeasurementColumn(DataTest):
    def setUp(self):
        super(MeasurementColumn, self).setUp()
        self.col = Table.MeasurementColumn(
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
        self.dataColumn = Table.MeasurementColumn(
            self.dataSymbol,
            ("m³", self.unit),
            self.data
        )
        self.derivColumn = Table.DerivatedColumn(
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
        self.dataColumn2 = Table.MeasurementColumn(
            self.dataSymbol2,
            ("m/s^2", units.meter/(units.second**2)),
            [value*(units.mile/(units.hour**2)) for value in range(10)]
        )
        self.derivSymbol2 = sympy.Symbol("F")
        self.derivColumn2 = Table.DerivatedColumn(
            self.derivSymbol2,
            ("N", units.newton),
            [self.dataColumn2, self.derivColumn],
            self.symbol * self.dataSymbol2
        )
        self.derivColumn2.update(True)
        finalData = [(value*(units.mile**3)*(units.kilogram/(units.meter**3))*value*units.mile/(units.hour**2) / (units.newton), {}) for value in range(10)]
        self.assertEqual(list(self.derivColumn2), finalData)


class TableTest(unittest.TestCase):
    def setUp(self):
        table = Table.Table()
        self.table = table
        
        lengthSymbol = sympy.Symbol("x")
        lengthData = [value*units.m for value in range(10)]
        table.add(Table.MeasurementColumn(
            lengthSymbol,
            ("m", units.m),
            lengthData
        ))
        self.lengthSymbol, self.lengthData = lengthSymbol, lengthData
        
        timeSymbol = sympy.Symbol("t")
        timeData = [value*units.s for value in range(10)]
        table.add(Table.MeasurementColumn(
            timeSymbol,
            ("s", units.s),
            timeData
        ))
        self.timeSymbol, self.timeData = timeSymbol, timeData

        volumeSymbol = sympy.Symbol("V")
        volumeData = [value*units.m**3 for value in range(10)]
        table.add(Table.MeasurementColumn(
            volumeSymbol,
            ("m³", units.m**3),
            volumeData
        ))
        self.volumeSymbol, self.volumeData = volumeSymbol, volumeData
        
        massSymbol = sympy.Symbol("m")
        massData = [value*units.kg for value in range(1, 11)]
        table.add(Table.MeasurementColumn(
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
