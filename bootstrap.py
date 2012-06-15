#!/usr/bin/python3
import sys
import argparse
import os
import stat

if __name__ == "__main__":
    PROGNAME = os.path.basename(sys.argv[0])
    
    parser = argparse.ArgumentParser(
        description="""\
Bootstrap a experiment evaluation script. The script is stored to
SCRIPTFILE. It is assumed that you want to read our gnuplot-compatible
format data from DATAFILE, but if not that's easy to change. Furthermore
you can specify an arbitary amount of symbols which will be pulled from
the table into the local namespace."""
    )
    parser.add_argument(
        "scriptfile",
        metavar="SCRIPTFILE",
        help="Name of the script file to create."
    )
    parser.add_argument(
        "-f", "--force",
        dest="force",
        default=False,
        action="store_true",
        help="You may use the --force to overwrite the target scriptfile. Default is off, to protect you from overwriting your data."
    )
    parser.add_argument(
        "-p", "--praktool-dir",
        metavar="PATH",
        dest="praktoolDir",
        default=None,
        help="Path to the praktool package (only if it's not in your python path)"
    )
    parser.add_argument(
        "datafile",
        metavar="DATAFILE",
        help="Name of the datafile to read."
    )
    parser.add_argument(
        "symbol",
        nargs="*",
        help="Symbols to import into the local namespace"
    )

    args = parser.parse_args(sys.argv[1:])

    if os.path.exists(args.scriptfile):
        if os.path.isfile(args.scriptfile) and not args.force:
            print("{0}: scriptfile {1!r} already exists, use the --force luke.".format(PROGNAME, args.scriptfile))

    out = open(args.scriptfile, "w")
    template = """\
#!/usr/bin/python
# encoding=utf-8

from __future__ import division, print_function

import itertools
import sys{0}

import sympy as sp
import sympy.physics.units as units

import Evaluation.Table as Table
import Evaluation.TableParser as Parser
import Evaluation.StatUtils as StatUtils
from Document.TablePrinter import SimplePrinter, LaTeXPrinter
from Evaluation.ValueClasses import StatisticalUncertainty, SystematicalUncertainty
import CODATA
CODATA.patchUnits()

data = Table.Table(Parser.ParseGnuplot(open("{1}", "r")))

"""
    if args.praktoolDir is not None:
        pathInjection = "\nsys.path.append({0})".format(repr(args.praktoolDir))
    else:
        pathInjection = ""
    out.write(template.format(pathInjection, args.datafile))

    if len(args.symbol) > 0:
        template = "{0} = (col.symbol for col in map(data.__getitem__, ({1}, )))\n"
        out.write(template.format(
            ", ".join(args.symbol),
            ", ".join(map(repr, args.symbol))
        ))
    template = """\

if __name__ == "__main__":
    # this must be called before data in any derivated columns is accessed
    data.updateAll()
"""
    out.write(template)
    if len(args.symbol) > 0:
        template = "    SimplePrinter([{0}])(data, file=sys.stdout)\n"
        out.write(template.format(
            ", ".join(map(repr, args.symbol))
        ))
    out.close()

    os.chmod(args.scriptfile, os.stat(args.scriptfile).st_mode | stat.S_IXUSR | stat.S_IXOTH | stat.S_IXGRP)
else:
    raise ImportError("Thou shalt not import this script.")
