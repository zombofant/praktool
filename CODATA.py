"""
CODATA constants.
"""

import sympy.physics.units as u
import sympy as sp

e = u.eV / u.V
me = 910938215*u.kg*1/(10**39)
mp = 1672621637*u.kg*1/(10**36)

def patchUnits(u):
    def patchUnits():
        u.e = e
        u.me = me
        u.mp = mp
    return patchUnits
patchUnits = patchUnits(u)

del u
