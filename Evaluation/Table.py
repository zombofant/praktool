# encoding=utf-8
from __future__ import unicode_literals, division, print_function
from our_future import *

import abc
import itertools

import sympy.physics.units as units

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
        for col in columns:
            self.unitDict[col.symbol] = col.unitExpr
        self.units = self.unitDict.items()

        self.indexIter = iter(xrange(l))

    def __iter__(self):
        return self

    def next(self):
        i = next(self.indexIter)
        values = dict()
        for symbol, iterable in self.myColumns:
            values[symbol] = next(iterable)
        print(values)
        return values


class QuantityIterator(object):
    def __init__(self, dataiter, unit):
        self._dataiter = dataiter
        self.unit = unit

    def next(self):
        return next(self._dataiter)


class TableColumn(object):
    """
    Represents a column in a :class:`Table`.

    *symbol* must be a sympy :class:`sympy.core.symbol.Symbol` which identifies
    the value in the column. *title* can be set if the string representation of
    *symbol* is not suitable as a title for the column.

    *displayUnit* must either be a string which can be evaluated to a sympy
    expression using `eval(displayUnit, sympy.physics.units.__dict__)` or a
    container like `(unitName, unitExpr)`, with *unitName* being the plain text
    name of the unit and *unitExpr* being a sympy expression resembling the
    unit.

    *defaultMagnitude* can be a unitless sympy expression which is then used to
    scale the final quantities. If this is `None`, automatic scaling takes
    place.

    One can create an iterable over the rows of a table column by calling
    :func:`iter` on a :class:`TableColumn` instance.

    You may override the :func:`TableColumn.dataHash` method to reflect changes
    in the data stored in the column. This helps for caching calculated data.
    You may return a value of arbitary type, but it must be hashable and
    comparable. If you do not the columns contents to be cached, return
    `NotImplemented`.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, symbol, displayUnit, defaultMagnitude=None, title=None, **kwargs):
        super(TableColumn, self).__init__(**kwargs)
        self.symbol = symbol
        self.title = title or unicode(symbol)
        try:
            if isinstance(displayUnit, (unicode, str)):
                raise TypeError()  # ugly, but avoids code duplication
            self.unit, self.unitExpr = displayUnit
        except TypeError:
            self.unit = displayUnit
            self.unitExpr = eval(unicode(displayUnit), units.__dict__)
        if defaultMagnitude is None:
            raise NotImplementedError("Cannot scale automagically yet.")
        self.magnitude = defaultMagnitude

    @abc.abstractmethod
    def __iter__(self):
        pass

    @abc.abstractmethod
    def __len__(self):
        pass

    def dataHash(self):
        return NotImplemented

    def iterDisplay(self):
        unitName = self.unit
        unify = 1 / self.magnitude
        for row in self:
            yield (row * unify, unitName)


class MapColumn(TableColumn):
    def __init__(self, symbol, unit, operation, defaultMagnitude=None,
            title=None, **kwargs):
        super(MapColumn, self).__init__(symbol, unit,
            defaultMagnitude=defaultMagnitude, title=title, **kwargs)
        if not hasattr(operation, "__call__"):
            raise TypeError("operation must be callable.")
        self.operation = operation if operation is not Identity else None

    def _mapSingle(self, data):
        return self.operation(data) / self.unitExpr

    def mapSingle(self, data):
        op = self.operation
        if op is None:
            return data / self.unitExpr
        else:
            return op(data) / self.unitExpr

    def _mapData(self, data):
        if self.operation is None:
            unitExpr = self.unitExpr
            return itertools.imap(lambda x: x / unitExpr, data)
        return itertools.imap(self.operation, data)


class DataColumn(MapColumn):
    """
    Implements a raw data column.

    *data* must be a iterable of sympy expressions resembling the data
    including its units. The iterable will only be evaluated once, mapped with
    *operation* and stored as list internally.
    """
    def __init__(self, symbol, unit, data, operation=Identity,
            defaultMagnitude=None, title=None, **kwargs):
        super(DataColumn, self).__init__(symbol, unit, operation,
            defaultMagnitude=defaultMagnitude, title=title, **kwargs)
        self.data = list(self._mapData(data))

    def __iter__(self):
        return QuantityIterator(iter(self.data), self.unitExpr)

    def __len__(self):
        return len(self.data)

    def dataHash(self):
        return self.data

    def appendRow(self, data):
        self.data.append(self.mapSingle(data))


class CachedColumn(TableColumn):
    def __init__(self, symbol, unit, referenceColumns, **kwargs):
        super(CachedColumn, self).__init__(symbol, unit, **kwargs)
        self.referenceColumns = frozenset(referenceColumns)
        # self.cacheToken =

    def getReference(self, referenceColumn):
        # no caching yet :)
        return referenceColumn.__iter__()


class DerivatedColumn(CachedColumn):
    def __init__(self, symbol, unit, referenceColumns, sympyExpr, defaultMagnitude=None,
            title=None, **kwargs):
        super(DerivatedColumn, self).__init__(symbol, unit, referenceColumns,
            defaultMagnitude=defaultMagnitude, title=title, **kwargs)
        self.sympyExpr = sympyExpr

    def __len__(self):
        return max((len(col) for col in self.referenceColumns))

    def __iter__(self):
        iterator = ColumnsIterator(self.referenceColumns)
        unitExpr = self.sympyExpr.subs(iterator.units)
        return QuantityIterator(itertools.imap(lambda x: x / unitExpr, itertools.imap(self.sympyExpr.subs, iterator)), unitExpr)


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

    def add(self, column):
        # look closer ... closer ... SETDEFAULT!
        if not self.columns.setdefault(column.symbol, column) is column:
            raise KeyError("Duplicate symbol: {0}".format(column.symbol))
        self.symbolNames[unicode(column.symbol)] = column.symbol

    def __getitem__(self, symbol_or_name):
        if isinstance(symbol_or_name, (unicode, str)):
            return self.columns[self.symbolNames[symbol_or_name]]
        else:
            return self.columns[symbol_or_name]

    def __delitem__(self, symbol_or_name):
        if isinstance(symbol_or_name, (unicode, str)):
            symbol = self.symbolNames[symbol_or_name]
        else:
            symbol = symbol_or_name
        del self.symbolNames[unicode(symbol)]
        del self.columns[symbol]

