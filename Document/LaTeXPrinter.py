# encoding=utf-8
from __future__ import unicode_literals, division, print_function
from our_future import *

import abc
import sys
import itertools

from Document.TablePrinter import TablePrinter

class LaTeXPrinter(TablePrinter):
    def __init__(self, columnKeys, alignment=None, precision=6, **kwargs):
        super(LaTeXPrinter, self).__init__(columnKeys, **kwargs)
        self._format = "{{0:.{0}f}}".format(precision)
        self._secondaryFormat = "{{0:.{0}f}}".format(precision)
        self._alignment = alignment or 'r' * len(columnKeys)

    def printColumns(self, columns, file=sys.stdout, encoding="utf-8"):

        tableData = itertools.izip(*columns)
        for row in tableData:
            print(' '.join(map(self.formatField, row)).encode(encoding), file=file)

    def printColumns(self, columns, file=sys.stdout, encoding="utf-8"):
        print(r'\begin{{tabular}}{{{0}}}'.format(self._alignment).encode(encoding), file=file)

        print(r'\toprule'.encode(encoding), file=file)
        print(' & '.join('{0}/{1}'.format(str(column.symbol).decode("utf-8"), str(column.unit).decode("utf-8")) for column in columns).encode(encoding), end=b'\\\\\n', file=file)
        print(r'\midrule'.encode(encoding), file=file)
        tableData = itertools.izip(*columns)
        for row in tableData:
            print(' & '.join(map(self.formatField, row)).encode(encoding), file=file, end=b'')
            print(r'\\'.encode(encoding), file=file)
        print(r'\bottomrule'.encode(encoding), file=file)

        print(r'\end{tabular}'.encode(encoding), file=file)
