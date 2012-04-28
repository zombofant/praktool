import sympy as sp

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

    return res, sp.sqrt(res2 - res**2)
