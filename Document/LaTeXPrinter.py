# encoding=utf-8
from __future__ import unicode_literals, division, print_function
from our_future import *

import abc
import sys
import itertools
import functools

from Document.TablePrinter import TablePrinter
import Evaluation.StatUtils as StatUtils

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

    def siunitx_encode(self, unitexpr):
        # no, thats not perl
        return ("\\"+unitexpr.replace("*", "\\").replace("/", "\\per\\"))\
                            .replace("\\1", "")

    def printColumns(self, columns, file=sys.stdout, encoding="utf-8"):
        print(r'\begin{{tabular}}{{{0}}}'.format(self._alignment).encode(encoding), file=file)

        print(r'\toprule'.encode(encoding), file=file)
        print(' & '.join('${0}\,\,[\si{{{1}}}]$'.format(self.map_symbol(str(column.symbol).decode("utf-8")), self.siunitx_encode(str(column.unit).decode("utf-8"))) for column in columns).encode(encoding), end=b'\\\\\n', file=file)
        print(r'\midrule'.encode(encoding), file=file)
        tableData = itertools.izip(*columns)
        for row in tableData:
            print(' & '.join(map(self.formatField, row)).encode(encoding), file=file, end=b'')
            print(r'\\'.encode(encoding), file=file)
        print(r'\bottomrule'.encode(encoding), file=file)

        print(r'\end{tabular}'.encode(encoding), file=file)

class siunitxPrinter(object):
    _dummy_attachment_iter = itertools.repeat(None)

    def __init__(self, column_keys,
            precision=None,
            column_precision={},
            attachment=None,
            attachments=[],
            column_opts={},
            symbol_map={},
            booktabs=True,
            **kwargs):
        super(siunitxPrinter, self).__init__(**kwargs)
        self._column_keys = column_keys
        self._column_precision = column_precision
        self._attachment = attachment
        if attachment is None:
            if len(attachments) > 1:
                raise ValueError("Sorry, {} only supports only one attachment".format(type(self).__name__))
            self._attachment = next(iter(attachments))
        else:
            if attachments:
                raise ValueError("{} attachment must be set by only one of ``attachment`` and ``attachments`` kwargs.".format(type(self).__name__))
        self._column_opts = column_opts
        self._symbol_map = symbol_map
        self._precision = precision
        self._booktabs = booktabs

    def get_column_precision(self, column):
        return self._column_precision.get(column.symbol, None) or self._precision

    def _format_column_values(self, column):
        precision = self.get_column_precision(column)
        if self._attachment is not None:
            attachment_iter = column.attachments.get(self._attachment, self._dummy_attachment_iter)
        else:
            attachment_iter = self._dummy_attachment_iter

        for value, attachment in zip(column.data, attachment_iter):
            if attachment is not None:
                yield StatUtils.error_rounding(value, attachment, force_digits=precision)
            else:
                yield StatUtils.digit_rounding(value, precision), None

    def _format_cell(self, vstr, dvstr):
        if dvstr is None:
            return vstr
        else:
            return vstr + " +- " + dvstr

    def _siunitx_unit(self, unit):
        # no, thats not perl
        return ("\\"+str(unit).replace("*", "\\").replace("/", "\\per\\"))\
                            .replace("\\1", "")

    def _process_column(self, column):
        coltype = "S"
        try:
            coltype += "[" + self._column_opts[column.symbol] + "]"
        except KeyError:
            pass

        unitstr = self._siunitx_unit(column.unit)
        symb = self._symbol_map.get(str(column.symbol), str(column.symbol))
        if unitstr:
            header = r"{{${symb!s}\,\,[\si{{{unitstr}}}]$}}".format(
                symb=symb,
                unitstr=unitstr
            )
        else:
            header = r"{{${symb!s}$}}".format(
                symb=symb
            )

        return coltype, header, [self._format_cell(v, dv) for v, dv in self._format_column_values(column)]

    def _process_columns(self, column_dict):
        return list(map(
            self._process_column,
            (column_dict[key] for key in self._column_keys)
        ))

    def _output_lines(self, table):
        column_info = list(zip(*self._process_columns(table)))
        types = column_info[0]
        headers = column_info[1]
        iterables = column_info[2]

        yield r"\begin{tabular}{" + "".join(types) + "}"

        if self._booktabs:
            yield r"\toprule"

        yield " & ".join(headers) + r" \\"

        if self._booktabs:
            yield r"\midrule"

        for cells in zip(*iterables):
            yield " & ".join(cells) + r" \\"

        if self._booktabs:
            yield r"\bottomrule"

        yield r"\end{tabular}"


    def __call__(self, table, file=sys.stdout, encoding="utf-8"):
        file.write("\n".join(self._output_lines(table)).encode(encoding))

