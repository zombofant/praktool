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
    """
    Represents a set of data points in a Table object. These may be
    virtual (i.e. created on the fly by :meth:`update`) or static (i.e.
    given by the user at creation time or inserted manually).

    The end-user will probably want to use :cls:`MeasurementColumn` and
    :cls:`DerivatedColumn` mainly, probably by using the more convenient
    interface provided by :cls:`Table`.

    *symbol* is expected to be a sympy symbol which is used to reference
    the column. This mainly has effect when used with a Table and for
    derivating columns from other columns.

    *unit* must be one of the following
    * a string which can be parsed into a unit by using only identifiers
      declared in the :mod:`sympy.physics.units` module
    * a sympy expression which contains units
    * a tuple of a string used as display-name for the unit and a sympy
      expression which represents the unit.

    If only the sympy expression is given, it will be converted into a
    string to be used as display name. This will most likely look ugly,
    so its recommended to supply a nice name for the unit yourself.

    *magnitude* can be a factor which is applied when printing the
    column, but this is mostly obsolete by now.
    """
    
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

    def attach(self, key, default=None):
        """
        Attach a uncertainty to the column.

        *key* must be a derivate of :cls:`Uncertainty` or similar. If an
        attachment with the given *key* already exists, it is rejected
        with a *KeyError*.

        *default* may be given if the column does not contain any data
        yet, but is mandatory if there is already data in the column.
        *default* is used to fill any unset values for the attachment,
        for example when adding new values to the column which do not
        specify the value for the attachment or if there are already
        values in the column.

        *default* may be *None*, but this will raise a ValueError if
        any unspecified values occur (i.e. appending values without
        attachment information or already existing values).
        """
        if key in self.attachments:
            raise KeyError("Attachment {0} already defined".format(key))
        self.attachments[key] = ColumnAttachment(key, default=default, initialLength=len(self))

    newAttachment = attach

    def relAttach(self, key, factor, additive=True):
        if not key in self.attachments:
            self.attach(key, 0.)
        elif not additive:
            self.attachments[key].data = [0] * len(self)
        targetList = self.attachments[key].data
        for i, value in enumerate(self.data):
            targetList[i] += value * factor

    def clear(self):
        """
        Delete all data from the column.
        """
        self.attachments = {}
        self.data = []

    def rawAppend(self, value, attachments=None):
        """
        Append a value, possibly with attachments, to the column.

        *value* must be the unitless representation of the value, in
        units of :attr:`unitExpr`. In the future, adding a value
        which contains units may raise an exception. Currently, it will
        certainly wreak havoc on your calculations.

        *attachments* may be a `dict` or *None*. If it's a `dict`, the
        keys must be valid attachment keys and present in the object.
        If an attachment key is not defined but declared in the object,
        the default value will be used (if any). If no default value
        has been specified for a given attachment, a *ValueError* will
        be raised.
        """
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

    _append = rawAppend

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
        """
        This must be overriden by derivated classes to specify their
        behaviour on updating.

        *forceDeep* may be set to True. If that is the case, a column
        must force all columns it depends on to update too. This will
        not be the case during normal operation, as a dependency graph
        is used to calculate the optimal updating route.
        """

    def mean(self):
        """
        Calculate the mean value and the standard deviation of the
        column using :func:`StatUtils.mean` and return those including
        the unit suffix.
        """
        value, stddev = StatUtils.mean(self.data)
        return value * self.unitExpr, stddev * self.unitExpr


class MeasurementColumn(Column):
    """
    The measurement column holds static values created by measurement.
    Nevertheless it may be manipulated during script runtime by the
    application. An end-user will probably not want to create such a
    column by hand, but use a :mod:`TableParser` to read a data file.

    *symbol* and *unit* are the same as for :cls:`Column`.

    *data* may be an iterable which is appended to the column right at
    the beginning.

    If *noUnits* is set to `True` (default is `False`), it will be
    assumed that the data given in *data* is in units of the Column and
    thus must not be treated specially. Also no transformation for
    nested iterables (see :meth:`append`) will be made.
    """
    
    def __init__(self, symbol, unit, data=None, magnitude=1, noUnits=False, **kwargs):
        super(MeasurementColumn, self).__init__(symbol, unit,
            magnitude=magnitude, **kwargs)
        if data is not None:
            if noUnits:
                collections.deque(map(self.rawAppend, data), maxlen=0)
            else:
                collections.deque(map(self.append, data), maxlen=0)

    def append(self, row):
        """
        Convenience function to append a row to the column.

        *row* must be one of the following:
        * a numeric expression, including a sumpy expression. It will be
          assumed to have a unit attached, so it will be divided by
          :attr:`unitExpr`.
        * an iterable of numeric values like above. All values will be
          made unitless and the mean is added to the column. If
          declared, the attachment for statistical uncertainty will be
          set to the standard deviation of the mean.
        """
        if isinstance(row, (float, int, long, sp.Expr)):
            self.rawAppend(row / self.unitExpr)
        elif hasattr(row, "__iter__"):
            unitExpr = self.unitExpr
            mean, stddev = StatUtils.mean(map(lambda x: x / unitExpr, row))
            self.rawAppend(mean, {
                ValueClasses.StatisticalUncertainty: stddev
            })
        else:
            raise TypeError("Row must be ((numeric or sympy) expr for single values or iterable) for automatic statistics")

    def update(self, forceDeep=False):
        pass


class DerivatedColumn(Column):
    """
    Manages derivation of data from other columns. An end-user will
    probably not want to create a column of this type manually but use
    the convenient interface of :cls:`Table`.

    *symbol* and *unit* are the same as for :cls:`Column`.

    *expression* must be an sympy expression with unknowns which
    represent the values of other columns. 

    *sources* must be an iterable of columns on which the given
    expression depends.
    """
    
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
            self.rawAppend(value, attachmentDict)


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
