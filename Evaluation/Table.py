# encoding=utf-8
from __future__ import unicode_literals, division, print_function
from our_future import *

import abc
import sys
import itertools
import functools
import collections

import sympy as sp
import sympy.physics.units as units
import numpy as np

import utils
import sympyUtils

import StatUtils
import ValueClasses

class Identity(object):
    """
    Used as a magic value for bypassing the operation of MapColumn objects.
    """


class ColumnsIterator(object):
    """
    Iterate over a sequence of columns and yield dict compatible to sympys subs
    method for each row in the columns.

    Stops as soon as the first column runs out of data. Throws a ValueError
    exception if the columns have different :func:`len` values.
    """
    
    def __init__(self, columns):
        self.columns = columns
        l = len(next(iter(columns)))
        self.myColumns = [(column.symbol, iter(column)) for column in columns]
        self.unitDict = dict()
        self.errorSymbols = []
        self.attachments = set()
        for col in columns:
            symbol = col.symbol
            self.unitDict[symbol] = symbol * col.unitExpr
            self.errorSymbols.append((symbol, sp.Dummy(b"delta__"+str(symbol))))
            self.attachments.update(col.attachments.iterkeys())
        self.units = self.unitDict.items()
        self.errorSymbolDict = dict(self.errorSymbols)

        self.indexIter = iter(xrange(l))

    def __iter__(self):
        return self

    def next(self):
        i = next(self.indexIter)
        values = dict()
        attachments = dict()
        for symbol, iterable in self.myColumns:
            value, attachmentValues = next(iterable)
            values[symbol] = value
            errorSymbol = self.errorSymbolDict[symbol]
            for key, value in attachmentValues.iteritems():
                attachments.setdefault(key, dict())[errorSymbol] = value
        return values, attachments


class QuantityIterator(object):
    def __init__(self, dataiter, unit, len=0):
        self._dataiter = dataiter
        self.unit = unit
        self.len = len
        self.i = 0

    def setLen(self, len):
        self.len = len

    def next(self):
        if self.len:
            if self.i % 10 == 0:
                print("Calculating: {0} / {1}".format(self.i, self.len), end="\r", file=sys.stderr)
                sys.stderr.flush()
            self.i += 1
        return next(self._dataiter)

    def __iter__(self):
        return self


class ColumnAttachment(object):
    def __init__(self, key, default=None, initialLength=0):
        self.key = key
        self.default = default or key.getDefault
        if initialLength > 0 and default is None:
            raise ValueError("Cannot create attachment without default value and with initial length")
        self.data = [default] * initialLength

    def append(self, value):
        self.data.append(value)

    def appendDefault(self):
        if self.default is None:
            raise ValueError("Must have a value for attachment {0} (no default given)")
        self.data.append(self.default)

    def __iter__(self):
        return iter(self.data)


class Column(object):
    def __init__(self, symbol, unit, magnitude=1, **kwargs):
        super(Column, self).__init__(**kwargs)
        self.attachments = dict()
        self.symbol = symbol
        try:
            if isinstance(unit, (unicode, str)):
                raise TypeError()  # ugly, but avoids code duplication
            if isinstance(unit, sp.Expr):
                raise ValueError()
            self.unit, self.unitExpr = unit
        except ValueError:
            self.unitExpr = unit
            self.unit = str(unit)
        except TypeError:
            self.unit = unit
            self.unitExpr = eval(unicode(unit), units.__dict__)
        if magnitude is None:
            raise NotImplementedError("Cannot scale automagically yet")
        self.magnitude = magnitude
        self.clear()

    def newAttachment(self, key, default=None):
        if key in self.attachments:
            raise KeyError("Attachment {0} already defined".format(key))
        self.attachments[key] = ColumnAttachment(key, default=default, initialLength=len(self))

    def clear(self):
        self.attachments = {}
        self.data = []

    def _append(self, value, attachments=None):
        for key, value in self.attachments.iteritems():
            if key in attachments:
                self.attachments[key].append(value)
            else:
                self.attachments[key].appendDefault()
        self.data.append(value)

    def __iter__(self):
        l = len(self.data)
        keyIterators = list()
        for key, value in self.attachments.iteritems():
            assert len(value) == l
            keyIterators.append((key, iter(value)))
        
        for row in self.data:
            attachments = dict()
            for key, iterator in keyIterators:
                attachments[key] = next(iterator)
            yield row, attachments

    def __len__(self):
        return len(self.data)
    
    def getSources(self):
        return []

    @abc.abstractmethod
    def update(self, forceDeep=False):
        pass


class MeasurementColumn(Column):
    def __init__(self, symbol, unit, data=None, magnitude=1, noUnits=False, **kwargs):
        super(MeasurementColumn, self).__init__(symbol, unit,
            magnitude=magnitude, **kwargs)
        if data is not None:
            if noUnits:
                collections.deque(map(self._append, data), maxlen=0)
            else:
                collections.deque(map(self.append, data), maxlen=0)

    def append(self, row):
        if isinstance(row, (float, int, long, sp.Expr)):
            self._append(row / self.unitExpr)
        elif hasattr(row, "__iter__"):
            unitExpr = self.unitExpr
            mean, stddev = StatUtils.mean(map(lambda x: x / unitExpr, row))
            self._append(mean, {
                ValueClasses.StatisticalUncertainity: stddev
            })
        else:
            raise TypeError("Row must be ((numeric or sympy) expr for single values or iterable) for automatic statistics")

    def update(self, forceDeep=False):
        pass


class DerivatedColumn(Column):
    def __init__(self, symbol, unit, sources, expression, magnitude=1, **kwargs):
        super(DerivatedColumn, self).__init__(symbol, unit, magnitude=magnitude)
        self.sources = frozenset(sources)
        self.expression = expression

    def getSources(self):
        return frozenset(self.sources)

    def update(self, forceDeep=False):
        if forceDeep:
            for source in self.sources:
                source.update(forceDeep=True)
        self.clear()
        iterator = ColumnsIterator(self.sources)
        unitfreeExpr = self.expression.subs(iterator.units) / self.unitExpr
        attachments = iterator.attachments
        if len(attachments) > 0:
            errorExpr = buildErrorExpression(unitfreeExpr, iterator.errorSymbols)

            for key in attachments:
                self.newAttachment(key, default=0)

        attachmentDict = dict()
        for valueSubs, attachmentSubs in iterator:
            attachmentDict.clear()
            value = unitfreeExpr.subs(valueSubs)
            for key in attachments:
                attachmentDict[key] = errorExpr.subs(valueSubs, attachmentSubs)
            self._append(value, attachmentDict)
            
        # return QuantityIterator(itertools.imap(unitfreeExpr.subs, iterator), self.unitExpr)


class Table(object):
    """
    Maintains a measurement table representation.
    """

    def __init__(self, columns=(), **kwargs):
        super(Table, self).__init__(**kwargs)
        self.columns = {}
        self.symbolNames = {}
        for column in columns:
            self.add(column)

    def symbolAvailable(self, symbol):
        if symbol in self:
            raise KeyError("Duplicate symbol: {0}".format(symbol))

    def add(self, column):
        # look closer ... closer ... SETDEFAULT!
        if not self.columns.setdefault(column.symbol, column) is column:
            raise KeyError("Duplicate symbol: {0}".format(column.symbol))
        self.symbolNames[unicode(column.symbol)] = column.symbol
        return column

    def derivate(self, symbol, unit, expression, defaultMagnitude=1, **kwargs):
        """
        Derivate a column from columns already stored in the table.

        *symbol* must be the symbol which is to be assigned to the new
        column, which must not be used inside the table yet.

        *unit* works like in :cls:`DataColumn`, but here it must be in
        its tuple form.

        *expression* is the expression which is used to calculate the
        cells of the column. It can contain any units or references to
        other columns you need, but the columns must be known in the
        table, otherwise a KeyError will be raised. If the expression
        does not evaluate to a unitless expression when all unknowns
        are substituted well and divided by the given *unit*, a
        ValueError will be raised (as this means that your expression
        does not yield the unit you requested).

        Return the new DerivatedColumn object.
        """
        self.symbolAvailable(symbol)
        
        symbols = set(sympyUtils.iterSymbols(expression))
        try:
            cols = list(map(self.__getitem__, symbols))
        except KeyError as err:
            raise KeyError("Unknown Symbol used in expression: {0}".format(err))
        
        unitName, unitExpr = unit
        
        unitSubsDict = dict((col.symbol, col.unitExpr) for col in cols)
        testUnitExpr = expression.subs(unitSubsDict)

        # this must have been excluded by the substitution
        assert utils.empty(iter(sympyUtils.iterSymbols(testUnitExpr)))
        
        if not utils.empty(iter(sympyUtils.iterSymbolsAndUnits(testUnitExpr / unitExpr))):
            raise ValueError("Unit of expression does not match requested unit.")
        
        column = self.add(DerivatedColumn(
            symbol,
            unit,
            cols,
            expression,
            defaultMagnitude=defaultMagnitude,
            **kwargs
        ))
        return column

    def diff(self, symbol_or_name, newSymbol):
        """
        Subtract subsequent items from the column with the given symbol
        or name and store the result in a new column with the given new
        symbol.

        This is equal to numerical forward differentiation, giving a new
        column with one item less than the previous column.

        Return the new DataColumn object
        """
        self.symbolAvailable(newSymbol)
        oldColumn = self[symbol_or_name]
        if len(oldColumn.attachments) > 0:
            raise ValueError("Can only diff columns without attachments")
        newData = np.diff(np.fromiter(oldColumn.data, np.float64))
        column = self.add(MeasurementColumn(
            newSymbol,
            (oldColumn.unit, oldColumn.unitExpr),
            newData,
            magnitude=oldColumn.magnitude,
            noUnits=True
        ))
        return column

    def __getitem__(self, symbol_or_name):
        if isinstance(symbol_or_name, (unicode, str)):
            return self.columns[self.symbolNames[symbol_or_name]]
        else:
            return self.columns[symbol_or_name]

    def __contains__(self, symbol_or_name):
        if isinstance(symbol_or_name, (unicode, str)):
            return symbol_or_name in self.symbolNames
        else:
            return symbol_or_name in self.columns

    def __delitem__(self, symbol_or_name):
        if isinstance(symbol_or_name, (unicode, str)):
            symbol = self.symbolNames[symbol_or_name]
        else:
            symbol = symbol_or_name
        del self.symbolNames[unicode(symbol)]
        del self.columns[symbol]
