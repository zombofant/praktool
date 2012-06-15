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
import Column
from Column import MeasurementColumn, DerivatedColumn

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

        Return the new :cls:`DerivatedColumn` object.
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
        
        column = self.add(Column.DerivatedColumn(
            symbol,
            unit,
            cols,
            expression,
            defaultMagnitude=defaultMagnitude,
            **kwargs
        ))
        return column

    def diff(self, symbol_or_name, newSymbol, offset=1, add=True):
        """
        Subtract subsequent items from the column with the given symbol
        or name and store the result in a new column with the given new
        symbol.

        *offset* specifies how many items are between the two items
        which are subtracted from each other.

        For `offset=1`, this is equal to numerical forward
        differentiation, giving a new column with one item less than the
        previous column.

        If *add* is set to *False*, the column will not be added to the
        table but returned only.

        Return the new :cls:`MeasurementColumn` object.
        """
        if add:
            self.symbolAvailable(newSymbol)
        oldColumn = self[symbol_or_name]
        if len(oldColumn.attachments) > 0:
            raise ValueError("Can only diff columns without attachments")
        newData = list(utils.diffNth(oldColumn.data, offset))
        
        column = Column.MeasurementColumn(
            newSymbol,
            (oldColumn.unit, oldColumn.unitExpr),
            newData,
            magnitude=oldColumn.magnitude,
            noUnits=True
        )
        if add:
            self.add(column)
        return column

    def integrate(self, symbol_or_name, newSymbol, offset=0, count=1, add=True):
        """
        Sums consecutive rows in the column identified by the given
        *symbol or name* and creates a new column with *newSymbol* from
        that.

        *count* items are added up together, starting from the
        *offset*th item. So for `offset=0, count=1` this is the identity
        operation.
        
        If *add* is set to *False*, the column will not be added to the
        table but returned only.
        
        Return the new :cls:`MeasurementColumn` object.
        """
        if add:
            self.symbolAvailable(newSymbol)
        oldColumn = self[symbol_or_name]
        if len(oldColumn.attachments) > 0:
            raise ValueError("Can only diff columns without attachments")
        newData = list(utils.intNth(oldColumn.data, count, offset=offset))
        
        column = Column.MeasurementColumn(
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
        """
        Joins several columns with similar content together. The cells
        of each row are joined together column-wise by calculating the
        mean. The statistical error gained from that is attached in the
        result column.

        Any uncertainty attachment on the source columns is **not**
        propagated for now.

        *addError* can be used to add a constant value to the estimated
        error calculated from the statistical operation.

        *propagateSystematical* can be set to *True* to enable
        rudimentary propagation of systematical uncertainties from the
        source columns. These are just averaged together and attached
        to the new column.

        Returns the new :cls:`MeasurementColumn` object.
        """
        sources = list(map(self.__getitem__, args))
        if len(args) < 2:
            raise ValueError("Join must have at least two columns to join")
        for source in sources:
            if len(source) == 0:
                source.update()
        column = Column.MeasurementColumn(
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
        """
        Updates all columns in the table. For this, a recursion is done
        through the dependency graph of the columns, updating them in
        optimal order and each column exactly once.

        If any cyclic references between columns occur or the graph is
        too deep (i.e. too many dependend columns), a ValueError is
        raised.
        """
        updated = set()
        try:
            for col in self.columns.itervalues():
                self._updateNode(col, updated)
        except RuntimeError:
            raise ValueError("Stack overflow; Cyclic reference between columns?")

    def __getitem__(self, symbol_or_name):
        if isinstance(symbol_or_name, Column.Column):
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
