# encoding=utf-8
from __future__ import unicode_literals, division, print_function

import warnings
import csv

import sympy
import sympy.physics.units

import Column

class Error(Exception):
    pass

def split_header_field(field):
    splitted = field.split(b'/', 1)
    if len(splitted) == 1:
        unit = "1"
        name = splitted[0]
    else:
        name, unit = splitted
    return name, unit

def ParseCSV(data, cols=None, dialect=None):
    """
    Parse a data file in the csv format.

    *data* is an iterable returning the lines of the file.

    If *cols* is not `None`, it has to be an sequence of
    :class:`Column.DataColumns`, if it is `None` the columns are
    generated from the first row of the file.

    *dialect* is passed to the `csv.reader` constructor as dialect
     argument.
    """
    # only handle the first line different if no cols are given
    first = cols is None
    for fields in csv.reader(lines, dialect=dialect):
        if first:
            for field in fields:
                name, unit = split_header_field(field)
                cols.append(Column.MeasurementColumn(sympy.Symbol(name), unit))
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

def ParseGnuplot(data, cols=None, annotation='%', header_sep=None,
        force_header=False):
    """
    Parse a data file in the gnuplot format with additional
    annotations for column names and units. Return the list of
    :class:`Column.DataColumns` objects.

    `#` is used to introduce comment line.

    *data* is an iterable returning the lines of the file.

    If *cols* is not `None`, it has to be an sequence of
    :class:`Column.DataColumns`, if it is `None` the columns are
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
        line = line.strip().decode("utf-8")
        if not line:
            continue

        if line.startswith('#') or force_header:
            if line.startswith('#' + annotation) or force_header:
                force_header = False
                if cols is None:
                    cols = []
                else:
                    warnings.warn('In file column specification ignored!')
                    continue
                if line.startswith('#' + annotation):
                    line = line[len(annotation)+1:]
                line = line.encode("ascii")
                fields = (x for x in line.strip().split(header_sep) if x)
                for field in fields:
                    name, unit = split_header_field(field)
                    cols.append(Column.MeasurementColumn(sympy.Symbol(name), unit, []))

            continue

        else:
            line = line.encode("ascii")
            fields = line.split()
            if len(fields) != len(cols):
                raise Error('Invalid Table: Incorrect number of columns')

            for col, field in zip(cols, fields):
                try:
                    dataItemAsNumber = int(field)
                except ValueError:
                    dataItemAsNumber = float(field)

                col.append(dataItemAsNumber * col.unitExpr)

    return cols
