import sympy as sp

def mean(data):
    """
    Calculate the arithmetic mean an standard deviation of the values
    in *data*, which should be an iterable of numeric (sympy compatible)
    values.

    Return the tuple `(mean, stddev)`
    """
    res = 0
    res2 = 0

    count = len(data)

    for item in data:
        a = item
        res += a
        res2 += a**2

    res /= count
    res2 /= count

    return res, sp.sqrt((res2 - res**2)/(count-1))

def buildErrorExpression(expr, symbols):
    """
    Take a sympy *expr* and a set of symbol tuples and return a gaussian
    error propagation expression.

    The symbol tuples must consist of `(symbol, dsymbol)`, where
    *symbol* is the symbol which references the actual value and
    *dsymbol* is the symbol which references a (possibly estimated)
    error value.
    """
    diffs = 0
    for symbol, dsymbol in symbols:
        diffs += (sp.diff(expr.subs(symbol, symbol), symbol) * dsymbol)**2
    return sp.sqrt(diffs)
