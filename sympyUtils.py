import sympy as sp
import sympy.physics.units as u

def iterSubtype(expr, type):
    if isinstance(expr, type):
        yield expr
        return
    for expr in expr.args:
        for symbol in iterSubtype(expr, type):
            yield symbol

def iterSymbols(expr):
    return iterSubtype(expr, sp.Symbol)

def iterUnits(expr):
    return iterSubtype(expr, u.Unit)

def iterSymbolsAndUnits(expr):
    return iterSubtype(expr, (sp.Symbol, u.Unit))

def setUndefinedTo(expr, value):
    return expr.subs(dict((sym, value) for sym in list(iterSymbols(expr))))
    
