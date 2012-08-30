"""
CODATA constants.
"""

import sympy.physics.units as u
import sympy as sp

e = u.eV / u.V
me = 910938215*u.kg*1/(10**39)
mp = 1672621637*u.kg*1/(10**36)
rydberg = ((e**2/(4*sp.pi*u.electric_constant))**2*(2*sp.pi**2*me/(u.planck**3*u.speed_of_light)))
planck2pi = u.planck / (2*sp.pi)
rydberg_energy = e**4*me/(2*(4*sp.pi*u.electric_constant*planck2pi)**2)

def patchUnits(u):
    def patchUnits():
        u.e = e
        u.me = me
        u.mp = mp
        u.rydberg = rydberg
        u.planck2pi = planck2pi
        u.rydberg_energy = rydberg_energy
    return patchUnits
patchUnits = patchUnits(u)

del u
