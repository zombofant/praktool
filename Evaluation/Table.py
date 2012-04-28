# encoding=utf-8
from __future__ import unicode_literals, division, print_function
from our_future import *

import abc
import itertools

import sympy.physics.units as units

import StatUtils
import ValueClasses

class Identity(object):
    """
    Used as a magic value for bypassing the operation of MapColumn objects.
    """


def iterColumns(columns):
    """
    Iterate over a sequence of columns and yield dict compatible to sympys subs
    method for each row in the columns.

    Stops as soon as the first column runs out of data. Throws a ValueError
    exception if the columns have different :func:`len` values.
    """
    l = len(next(iter(columns)))
    myColumns = [(column.symbol, iter(column)) for column in columns]
    for i in xrange(l):
        values = dict()
        for symbol, iterable in myColumns:
            values[symbol] = next(iterable)
        yield values


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
    def __init__(self, table, symbol, unit, magnitude=1, **kwargs):
        super(Column, self).__init__(**kwargs)
        self.attachments = dict()
        self.table = table
        self.symbol = symbol
        self.unitName, self.unitExpr = unit
        if magnitude is None:
            raise NotImplementedError("Cannot scale automagically yet")
        self.magnitude = magnitude

    def newAttachment(self, key, default=None):
        if key in self.attachments:
            raise KeyError("Attachment {0} already defined".format(key))
        self.attachments[key] = ColumnAttachment(key, default=default, initialLength=len(self))

    @abc.abstractmethod
    def __iter__(self):
        pass

    @abc.abstractmethod
    def __len__(self):
        pass


class MeasurementColumn(Column):
    def __init__(self, table, symbol, unit, magnitude=1, **kwargs):
        super(MeasurementColumn, self).__init__(self, table, symbol, unit,
            magnitude=magnitude)

    def _append(self, value, attachments=None):
        for key, value in self.attachments.iteritems():
            if key in attachments:
                self.attachments[key].append(value)
            else:
                self.attachments[key].appendDefault()
        self.data.append(value)

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
            raise TypeError("Row must be numeric or sympy expr for single values or iterable for automatic statistics")

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

class DerivatedColumn(Column):
    def __init__(self, table, symbol, sources, unit, magnitude=1, **kwargs):
        super(DerivatedColumn, self).__init__(self, table, symbol, unit, magnitude=magnitude)
        self.sources = sources

    
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
        unify = 1 / (self.unitExpr * self.magnitude)
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
        if self.operation is None:
            return data
        return self.operation(data)

    def _mapData(self, data):
        if self.operation is None:
            return data
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
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def dataHash(self):
        return self.data

    def appendRow(self, data):
        self.data.append(self._mapSingle(data))


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
        for rowValues in iterColumns(self.referenceColumns):
            yield self.sympyExpr.subs(rowValues)


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

