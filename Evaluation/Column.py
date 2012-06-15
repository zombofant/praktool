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
