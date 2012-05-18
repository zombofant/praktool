#!/usr/bin/python3
import sys
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "scriptfile",
        metavar="SCRIPTFILE",
        help="Name of the script file to create."
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
    print(args)

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
import Evaluation.ColumnOps as cops
from CODATA import patchUnits
patchUnits()

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
            ", ".join(repr(symbol) for symbol in args.symbol)
        ))
    template = """\

if __name__ == "__main__":
    pass
"""
    out.write(template)
    out.close()
    
    
else:
    raise ImportError("Thou shalt not import this script.")
