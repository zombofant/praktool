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
        self.default = default or key.getDefault()
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

    def __len__(self):
        return len(self.data)


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

    attach = newAttachment

    def clear(self):
        self.attachments = {}
        self.data = []

    def _append(self, value, attachments=None):
        if attachments is not None:
            for key, attachment in self.attachments.iteritems():
                attachmentValue = attachments.get(key, None)
                if attachmentValue is None:
                    attachment.appendDefault()
                else:
                    attachment.append(attachmentValue)
        else:
            for attachment in self.attachments.itervalues():
                attachment.appendDefault()
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
                ValueClasses.StatisticalUncertainty: stddev
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
        else:
            for source in self.sources:
                if len(source) == 0:
                    source.update()
        self.clear()
        iterator = ColumnsIterator(self.sources)
        unitfreeExpr = self.expression.subs(iterator.units) / self.unitExpr
        attachments = iterator.attachments
        if len(attachments) > 0:
            errorExpr = StatUtils.buildErrorExpression(unitfreeExpr, iterator.errorSymbols)

            for key in attachments:
                self.newAttachment(key, default=0)

        attachmentDict = dict()
        for valueSubs, attachmentSubs in iterator:
            attachmentDict.clear()
            value = unitfreeExpr.subs(valueSubs)
            for key in attachments:
                attachmentDict[key] = sympyUtils.setUndefinedTo(errorExpr.subs(valueSubs).subs(attachmentSubs[key]), 0)
            self._append(value, attachmentDict)


class ConstColumn(Column):
    def __init__(self, symbol, unit, value, attachments, length, magnitude=1, **kwargs):
        super(ConstColumn, self).__init__(symbol, unit, magnitude=magnitude)
        self.value = value / self.unitExpr
        if attachments:
            self.attachments = dict((key, value / self.unitExpr) for key, value in attachments.iteritems())
        else:
            self.attachments = {}
        self.length = length

    def __iter__(self):
        while True:
            yield (self.value, dict(self.attachments))

    def __len__(self):
        return self.length


class Table(object):
    """
    Maintains a measurement table representation.
    """

    @classmethod
    def Diff(cls, sourceTable, columnSymbols, offset=1, **kwargs):
        if offset < 1:
            raise ValueError("offset must be greater than or equal to 1. Got {0}".format(offset))
        symbols = [sourceTable[symbolName].symbol for symbolName in columnSymbols]
        columns = [sourceTable.diff(symbol, symbol, offset=offset, add=False) for symbol in symbols]
        return cls(columns=columns, **kwargs)

    @classmethod
    def Integrate(cls, sourceTable, columnSymbols, count=1, **kwargs):
        if count < 1:
            raise ValueError("count must be greater than or equal to 1. Got {0}".format(count))
        symbols = [sourceTable[symbolName].symbol for symbolName in columnSymbols]
        columns = [sourceTable.integrate(symbol, symbol, count=count, add=False) for symbol in symbols]
        return cls(columns=columns, **kwargs)

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

    @staticmethod
    def diffNth(iterable, n):
        i = 0
        iterator = iter(iterable)
        prev = next(iterator)
        for item in iterator:
            i += 1
            if i == n:
                i = 0
                yield item - prev
                prev = item

    @staticmethod
    def intNth(iterable, n):
        i = 0
        iterator = iter(iterable)
        s = next(iterator)
        for item in iterator:
            i += 1
            if i == n:
                i = 0
                yield s
                s = 0
            s += item

    def diff(self, symbol_or_name, newSymbol, offset=1, add=True):
        """
        Subtract subsequent items from the column with the given symbol
        or name and store the result in a new column with the given new
        symbol.

        This is equal to numerical forward differentiation, giving a new
        column with one item less than the previous column.

        Return the new DataColumn object
        """
        if add:
            self.symbolAvailable(newSymbol)
        oldColumn = self[symbol_or_name]
        if len(oldColumn.attachments) > 0:
            raise ValueError("Can only diff columns without attachments")
        newData = list(self.diffNth(oldColumn.data, offset))
        
        column = MeasurementColumn(
            newSymbol,
            (oldColumn.unit, oldColumn.unitExpr),
            newData,
            magnitude=oldColumn.magnitude,
            noUnits=True
        )
        if add:
            self.add(column)
        return column

    def integrate(self, symbol_or_name, newSymbol, count=1, add=True):
        """
        Return the new DataColumn object
        """
        if add:
            self.symbolAvailable(newSymbol)
        oldColumn = self[symbol_or_name]
        if len(oldColumn.attachments) > 0:
            raise ValueError("Can only diff columns without attachments")
        newData = list(self.intNth(oldColumn.data, count))
        
        column = MeasurementColumn(
            newSymbol,
            (oldColumn.unit, oldColumn.unitExpr),
            newData,
            magnitude=oldColumn.magnitude,
            noUnits=True
        )
        if add:
            self.add(column)
        return column

    def join(self, newSymbol, args, propagateSystematical=False, addError=0, newUnit=None):
        sources = list(map(self.__getitem__, args))
        if len(args) < 2:
            raise ValueError("Join must have at least two columns to join")
        for source in sources:
            if len(source) == 0:
                source.update()
        column = MeasurementColumn(
            newSymbol,
            (args[0].unit, args[0].unitExpr)
        )
        column.newAttachment(ValueClasses.StatisticalUncertainty, default=0)
        if propagateSystematical:
            column.newAttachment(ValueClasses.SystematicalUncertainty, default=0)
        for cells in itertools.izip(*args):
            values = list(map(lambda x: x[0], cells))
            mean, stddev = StatUtils.mean(values)
            attachmentDict = {}
            if propagateSystematical:
                syst = []
                for value, attachment in cells:
                    currSyst = attachment.get(ValueClasses.SystematicalUncertainty, None)
                    if currSyst is not None:
                        syst.append(currSyst)
                if len(syst) > 0:
                    attachmentDict[ValueClasses.SystematicalUncertainty] = sum(syst) / len(syst)
            attachmentDict[ValueClasses.StatisticalUncertainty] = stddev + addError
            column._append(mean, attachmentDict)
        self.add(column)

    def _updateNode(self, node, updated):
        if node in updated:
            return
        for source in node.getSources():
            if not source in updated:
                self._updateNode(source, updated)
                assert source in updated
        node.update()
        updated.add(node)

    def updateAll(self):
        updated = set()
        try:
            for col in self.columns.itervalues():
                self._updateNode(col, updated)
        except RuntimeError:
            raise ValueError("Stack overflow; Cyclic reference between columns?")

    def __getitem__(self, symbol_or_name):
        if isinstance(symbol_or_name, Column):
            return self[symbol_or_name.symbol]
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
        raise TypeError("Deletion explicitly prohibited (would break the update tree).")
        #~ if isinstance(symbol_or_name, (unicode, str)):
            #~ symbol = self.symbolNames[symbol_or_name]
        #~ else:
            #~ symbol = symbol_or_name
        #~ del self.symbolNames[unicode(symbol)]
        #~ del self.columns[symbol]
