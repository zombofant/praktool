from __future__ import print_function

__all__ = ["mean", "propagate_eval"]

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
        diffs += (sp.diff(expr, symbol) * dsymbol)**2
    return sp.sqrt(diffs)

def propagate_eval(expr, values):
    """
    Return the result of *expr* with *values* and the result of the gaussian
    error propagation.

    *values* must be an iterable of tuples, each consisting of the symbol
    associated with the value, the value itself, the error to be propagated
    (can be zero) and an expression which resembles the unit of the value (can
    be 1).

    The return value is a tuple of the value gained from evaluating the
    expression itself and the error gained from applying gaussian error
    propagation using the given error values.
    """
    value_sub = [(symb, value*unit) for symb, value, _, unit in values]
    error_symbols = [sp.Dummy(b"delta_error_propagation_"+str(symb))
                     for symb, _, _, _ in values]
    symbol_map = [(symb, err_symb)
                  for err_symb, (symb, _, _, _) in zip(error_symbols, values)]
    error_sub = [(error_symb, error*unit)
                 for error_symb, (_, _, error, unit) in zip(error_symbols, values)]

    result_value = expr.subs(value_sub)

    error_expr = buildErrorExpression(
        expr,
        symbol_map
    )

    error_value = error_expr.subs(value_sub).subs(error_sub)

    return result_value, error_value

