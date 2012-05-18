# encoding=utf-8
from __future__ import unicode_literals, division, print_function
from our_future import *

import abc
import sys
import itertools

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
    def __init__(self, columnKeys, precision=6, width=12, **kwargs):
        super(SimplePrinter, self).__init__(columnKeys, **kwargs)
        self._format = "{{0:{0}.{1}f}}".format(width, precision)

    @staticmethod
    def toFloat(value):
        return value[0] if isinstance(value[0], (int, long, float)) else float(value[0].evalf())

    def printColumns(self, columns, file=sys.stdout):
        floatedColumns = [list(map(self.toFloat, col.iterDisplay())) for col in columns]
        # print(floatedColumns)
        tableData = itertools.izip(*floatedColumns)
        for row in tableData:
            print(' '.join(map(self._format.format, row)), file=file)
