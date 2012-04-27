# encoding=utf-8

import itertools

import sympy

def mean(column):
    """
    Calculate the arithmetic mean an standard deviation of the values
    in *column*, which should be an iterable.

    Return the tuple `(mean, stddev)`
    """
    res = 0
    res2 = 0

    for item in column:
        a = item
        res += a
        res2 += a**2

    res /= len(column)
    res2 /= len(column)

    return res, sympy.sqrt(res2 - res**2)

def linearRegression(table, cx, cy):
    """
    Linear regression.

    The values from the columns *cx*, *cy* of *table* are taken as
    points.

    Returns `((m, em), (n, en))` where `m` is the slope and `n` is the
    y-intercept, `em` and `en` are there respective errors.

    FIXME: `em` and `en` are currently always zero
    """
    b1, a1, c1 = 0.0, 0.0, 0.0
    b2, a2, c2 = 0.0, 0.0, 0.0

    s = 1.0

    for x, y in itertools.izip(table[cx], table[cy]):
        w = 1.0/(s*s)

        b1 += w
        a1 += x*w
        c1 += y*w

        b2 = a1
        a2 += x*x*w
        c2 += x*y*w

    det = b1*a2 - b2*a1

    m = (b1*c2 - b2*c1) / det
    n = (c1*a2 - c2*a1) / det

    return ((m, em), (n, en))
