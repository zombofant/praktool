# encoding=utf-8
from __future__ import unicode_literals, division, print_function
from our_future import *

import abc
import sys
import itertools
import sympy as sp

from Evaluation.ValueClasses import (
    StatisticalUncertainty, SystematicalUncertainty, Uncertainty)

class TablePrinter(object):
    defaultAttachments = [StatisticalUncertainty, SystematicalUncertainty]

    def __init__(self, columnKeys, attachments=defaultAttachments, merge=False,
            error_joiner="±",
            **kwargs):
        super(TablePrinter, self).__init__(**kwargs)
        self._columnKeys = columnKeys
        self.attachments = list(attachments)
        self._merge = merge
        self._error_joiner = error_joiner

    @abc.abstractmethod
    def printColumns(self, columns, file=sys.stdout):
        pass

    def __call__(self, table, file=sys.stdout):
        columns = list(map(table.__getitem__, self._columnKeys))
        self.printColumns(columns, file=file)

    @staticmethod
    def toFloat(value):
        return value if isinstance(value, (int, long, float)) else float(value.evalf())

    @staticmethod
    def sqr(value):
        return value**2

    def formatField(self, field):
        errorJoiner = self._error_joiner
        attachments = field[1]
        values = []
        values.extend(map(lambda x: attachments.get(x, 0), self.attachments))
        main = self._format.format(self.toFloat(field[0]))
        mid = (errorJoiner if len(values) > 0 else "")
        if self._merge:
            attachments = sp.sqrt(sum(map(self.sqr, map(self.toFloat, values))))
            attachments = self._secondaryFormat.format(float(attachments))
        else:
            attachments = (errorJoiner.join(map(self._secondaryFormat.format, map(self.toFloat, values))))
        return main+mid+attachments

    def __call__(self, table, file=sys.stdout):
        columns = list(map(table.__getitem__, self._columnKeys))
        self.printColumns(columns, file=file)


class SimplePrinter(TablePrinter):
    def __init__(self, columnKeys, precision=6, width=12, **kwargs):
        precision = int(precision)
        super(SimplePrinter, self).__init__(columnKeys, **kwargs)
        self._format = "{{0:{0}.{1}f}}".format(width, precision)
        self._secondaryFormat = "{{0:.{0}f}}".format(precision)

    def printColumns(self, columns, file=sys.stdout, encoding="utf-8"):
        tableData = itertools.izip(*columns)
        for row in tableData:
            print(' '.join(map(self.formatField, row)).encode(encoding), file=file)
