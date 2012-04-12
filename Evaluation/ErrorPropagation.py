# encoding=utf-8

import sympy

def propagate(formula, *vars):
    """
    Calculate the error propagation formula for the sympy expression
    *formula* according to gaussian error progation, assuming
    uncorrelated measurements.

    *vars* is a list of tuples of the respective erroneous independent
     variables and the symbols used for their respective errors.
    """

    res = 0

    for var, err in vars:
        res += err ** 2 * sympy.diff(formula, var) ** 2

    return sympy.sqrt(res)
