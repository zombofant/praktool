# encoding=utf-8
from __future__ import unicode_literals, division, print_function
from our_future import *

import abc
import sys
import itertools

from Document.TablePrinter import TablePrinter

class GnuplotPrinter(TablePrinter):
    def __init__(self, columnKeys, alignment=None, precision=6, **kwargs):
        super(GnuplotPrinter, self).__init__(columnKeys, **kwargs)
        self._format = "{{0:.{0}f}}".format(precision)
        self._secondaryFormat = "{{0:.{0}f}}".format(precision)
        self._alignment = alignment or 'r' * len(columnKeys)

    def formatField(self, field):
        return super(GnuplotPrinter, self).formatField(field, errorJoiner=" ")

    def printColumns(self, columns, file=sys.stdout, encoding="utf-8"):
        tableData = itertools.izip(*columns)
        for row in tableData:
            print(' '.join(map(self.formatField, row)).encode(encoding), file=file, end=b'\n')
