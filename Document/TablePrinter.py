# encoding=utf-8
from __future__ import unicode_literals, division, print_function
from our_future import *

import abc
import sys
import itertools

from Evaluation.ValueClasses import (
    StatisticalUncertainity, SystematicalUncertainity, Uncertainity)

class TablePrinter(object):
    def __init__(self, columnKeys, **kwargs):
        super(TablePrinter, self).__init__(**kwargs)
        self._columnKeys = columnKeys

    @abc.abstractmethod
    def printColumns(self, columns, file=sys.stdout):
        pass

    def __call__(self, table, file=sys.stdout):
        columns = list(map(table.__getitem__, self._columnKeys))
        self.printColumns(columns, file=file)


class SimplePrinter(TablePrinter):
    defaultAttachments = [StatisticalUncertainity, SystematicalUncertainity]
    
    def __init__(self, columnKeys, attachments=defaultAttachments, precision=6, width=12, **kwargs):
        super(SimplePrinter, self).__init__(columnKeys, **kwargs)
        self._format = "{{0:{0}.{1}f}}".format(width, precision)
        self._secondaryFormat = "{{0:.{0}f}}".format(precision)
        self.attachments = list(attachments)

    @staticmethod
    def toFloat(value):
        return value if isinstance(value, (int, long, float)) else float(value.evalf())

    def formatField(self, field):
        attachments = field[1]
        values = []
        values.extend(map(lambda x: attachments.get(x, 0), self.attachments))
        main = self._format.format(self.toFloat(field[0]))
        mid = ("±" if len(values) > 0 else "")
        attachments = ("±".join(map(self._secondaryFormat.format, map(self.toFloat, values))))
        return main+mid+attachments

    def printColumns(self, columns, file=sys.stdout, encoding="utf-8"):
        # floatedColumns = [list(map(self.toFloat, col)) for col in columns]
        # print(floatedColumns)
        tableData = itertools.izip(*columns)
        for row in tableData:
            print(' '.join(map(self.formatField, row)).encode(encoding), file=file)
