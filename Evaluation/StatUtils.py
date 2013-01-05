from __future__ import print_function

__all__ = ["mean", "propagate_eval"]

import sympy as sp
import math

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

def propagate_eval(expr, values, out_unit=None):
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

def round_to_significant_digits(value, digits, exponent=None):
    if digits == 0:
        raise ValueError("Cannot round to 0 digits")
    if exponent is None:
        try:
            exponent = int(math.floor(math.log10(abs(value) / 4)))
        except ValueError:
            exponent = 1

    significant_digits = (digits - exponent) - 1

    factor = 10**(-significant_digits)
    value = round(value / factor) * factor

    fmt_digits = max(significant_digits, 0)

    return value, fmt_digits

def digit_rounding(v, digits):
    if digits is None:
        return "{}".format(v)
    else:
        value, fmt_digits = round_to_significant_digits(v, digits)
        return "{{:.{}f}}".format(fmt_digits).format(value)

def error_rounding(v, dv, force_digits=None):
    """
    Round and format the numeric value *v* to a string, treating the
    value *dv* as uncertainty on *v*. Return a tuple with the two
    strings, one resembling the rounded value of *v* and one resembling
    the rounded value of *dv*.

    If *force_digits* is not :data:`None`, it must be the integer number
    of significant digits which are to be displayed. If *force_digits*
    is :data:`None`, the amount of significant digits to be displayed
    is determined from *dv*.
    """
    v, dv = float(v), float(dv)
    try:
        err_exponent = int(math.floor(math.log10(abs(dv) / 4)))
    except ValueError:
        err_exponent = 1
    try:
        v_exponent = int(math.ceil(math.log10(abs(v))))
    except ValueError:
        v_exponent = err_exponent

    if force_digits is None:
        digits = (v_exponent - err_exponent) + 1
        if digits < 0:
            digits = 2
    else:
        digits = int(force_digits)

    v, fmt_digits = round_to_significant_digits(v, digits, v_exponent)
    dv, _ = round_to_significant_digits(dv, digits, v_exponent)

    fmt_str = "{{:.{digits}f}}".format(digits=fmt_digits)
    return fmt_str.format(v), fmt_str.format(dv)

def siunitx_number(vdv):
    """
    Take a tuple (*v*, *dv*) and format it as siunitx number *v* with
    uncertainty *dv* (without \\num macro).
    """
    return "{} +- {}".format(*vdv)

def siunitx_rounding(v, dv, siunit=None, force_digits=None, suggest_digits=None):
    """
    Produce the correct siunitx command to properly typeset the number
    *v* with uncertainty *dv* and optional siunitx unit expression
    *siunit*.

    Return the string containing the LaTeX macro which typesets the
    number correctly. Requires ``\\usepackage{siunitx}``.
    """
    if math.isnan(dv):
        numeric = digit_rounding(v, force_digits or suggest_digits or 3)
        if siunit:
            return r"\SI{"+numeric+"}{"+siunit+"}"
        else:
            return r"\num{"+numeric+"}"
    else:
        numeric = siunitx_number(error_rounding(v, dv, force_digits=force_digits))
        if siunit:
            return r"\SI{"+numeric+"}{"+siunit+"}"
        else:
            return r"\num{"+numeric+"}"

def siunitx_rounded_number(v, dv):
    return siunitx_number(error_rounding(v, dv))
