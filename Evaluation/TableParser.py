# encoding=utf-8
from __future__ import unicode_literals, division, print_function

import warnings
import csv

import sympy
import sympy.physics.units

import Table

class Error(Exception):
    pass

def ParseCSV(data, cols=None, dialect=None):
    """
    Parse a data file in the csv format.

    *data* is an iterable returning the lines of the file.

    If *cols* is not `None`, it has to be an sequence of
    :class:`Table.DataColumns`, if it is `None` the columns are
    generated from the first row of the file.

    *dialect* is passed to the `csv.reader` constructor as dialect
     argument.
    """
    # only handle the first line different if no cols are given
    first = cols is None
    for fields in csv.reader(lines, dialect=dialect):
        if first:
            for field in fields:
                name, unit = field.split(b'/', 1)
                cols.append(Table.DataColumn(sympy.Symbol(name), unit, [],
                                             defaultMagnitude=1))
        else:
            if len(fields) != len(cols):
                raise Error('Invalid Table: Incorrect number of columns')

            for col, field in zip(cols, fields):
                try:
                    dataItemAsNumber = int(field)
                except ValueError:
                    dataItemAsNumber = float(field)

                col.appendRow(dataItemAsNumber * col.unitExpr)

        first = False
    return cols

def ParseGnuplot(data, cols=None, annotation='%', header_sep=None):
    """
    Parse a data file in the gnuplot format with additional
    annotations for column names and units. Return the list of
    :class:`Table.DataColumns` objects.

    `#` is used to introduce comment line.

    *data* is an iterable returning the lines of the file.

    If *cols* is not `None`, it has to be an sequence of
    :class:`Table.DataColumns`, if it is `None` the columns are
    generated from the annotation in the file.

    *annotation* is the character used directly after `#` to introduce
    a column name and unit annotation.

    *header_sep* is the seperator used to split the column name and
     unit annotation. The default is `None`, so split is on any
     whitespace.

     A table could look like:

         #% t/s x/m
         0.0 0.0
         1.0 1.0
         2.0 4.0
         3.0 9.0
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
                    warnings.warn('In file column specification ignored!')
                    continue

                fields = line[2:].strip().split(header_sep)
                for field in fields:
                    name, unit = field.split(b'/', 1)
                    cols.append(Table.DataColumn(sympy.Symbol(name), unit, [],
                                                 defaultMagnitude=1))

            continue

        else:
            fields = line.split()
            if len(fields) != len(cols):
                raise Error('Invalid Table: Incorrect number of columns')

            for col, field in zip(cols, fields):
                try:
                    dataItemAsNumber = int(field)
                except ValueError:
                    dataItemAsNumber = float(field)

                col.appendRow(dataItemAsNumber * col.unitExpr)

    return cols
