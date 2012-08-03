# encoding=utf-8
from __future__ import unicode_literals, division, print_function
from our_future import *

import os
import re
from subprocess import Popen, PIPE

from Document.GnuplotPrinter import GnuplotPrinter

#re_m = re.compile("^m\s+=\s+([0-9]+\.[0-9]+)\s+\+/-\s+([0-9]+\.[0-9]+)\s+")
re_m = re.compile("^m\s+=\s+(-?[0-9]+\.[0-9]+)\s+\+/-\s+([0-9]+\.[0-9]+)\s+", re.M)
re_b = re.compile("^b\s+=\s+(-?[0-9]+\.[0-9]+)\s+\+/-\s+([0-9]+\.[0-9]+)\s+", re.M)

def linearRegression(table, colA, colB, errorAttachment=None):
    tmpfile = "/tmp/foo.{0}.plot".format(os.getpid())
    f = open(tmpfile, "w")
    GnuplotPrinter([table[colA], table[colB]], attachments=[errorAttachment])(table, file=f)
    f.close()

    f = open(tmpfile+".gp", "w")
    f.write("""\
fit m*x+b "{0}" using 1:3:2 via m, b""".format(
        tmpfile
    ))
    f.close()

    _, output = Popen(["gnuplot", tmpfile+".gp"], stderr=PIPE).communicate()
    output = output.decode()

    m = re_m.search(output).groups()
    b = re_b.search(output).groups()
    return tuple(map(float, m)), tuple(map(float, b))
    
