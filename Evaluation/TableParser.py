# encoding=utf-8
from __future__ import unicode_literals, division, print_function

import warning
import csv

import sympy
import sympy.physics.units

import Table

class Error(Exception):
    pass

def ParseCSV(data, cols):


def ParseGnuplot(data, cols=None, annotation='%', header_sep=None):
    """
    Parse a data file in the gnuplot format with additional
    annotations for column names and units.

    `#` is used to introduce comment line.

    *data* is an iterable returning the lines of the column.

    If *cols* is not `None`, it has to be an sequence of
    :class:`Table.DataColumns`, if it is `None` the columns are
    generated from the annotation in the file.

    *annotation* is the character used directly after `#` to introduce
    a column name and unit annotation.

    *header_sep* is the seperator used to split the column name and
     unit annotation. The default is `None`, so split is on any
     whitespace.
    """

    for line in data:
        line = line.strip()
        if not line:
            continue

        if line.startswith('#'):
            if line.startswith('#' + annotation):
                if cols is None:
                    cols = []
                else:
                    warning.warn('In file column specification ignored!')
                    continue

                cols = line[2:].strip().split(header_sep)
                for col in cols:
                    name, unit = col.split('/', 1)
                    col.append(Table.DataColumn(sympy.symbol(name), unit, []))

            continue

        else:
            lineData = line.split()
            if len(lineData) != len(cols):
                raise Error('Invalid Table: Uncorrect number of columns')

            for col, dataItem in zip(cols, lineData):
                try:
                    dataItemAsNumber = int(dataItem)
                except ValueError:
                    dataItemAsNumber = float(dataItem)

                col.appendRow(dataItemAsNumber * col.unitExpr)

        return cols
