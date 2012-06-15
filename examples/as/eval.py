#!/usr/bin/python
# encoding=utf-8
"""
In this experiment, we measured the angles at which interference pattern
lines occur in a simple interferometer. The angles were measured twice
to reduce errors introduced by reading the scale and so on, stored in
phi_i_deg and phi_i_min, where deg is the degree and min is the
degree-minute.

We also put the order of interference in the table, available as order,
also an elaborate guess on where in the balmer series the corresponding
line could be (n2).

The data is mangled to find the wavelength lambda with the statistical
error based on the data available. The constant g is available from a
previous part of the experiment and error propagated here for reference.
"""

from __future__ import division, print_function

import itertools
import sys
import os
sys.path.append("../../")

import sympy as sp
import sympy.physics.units as units

import Evaluation.Table as Table
import Evaluation.TableParser as Parser
import Evaluation.StatUtils as StatUtils
from Document.TablePrinter import SimplePrinter
from Evaluation.ValueClasses import StatisticalUncertainty, SystematicalUncertainty
import CODATA
CODATA.patchUnits()

# setup constant g from previous experiment
g = 1.536*10**-6*units.m

# some dummies for error propagation for g
order, lambda_, phi = sp.Dummy("order"), sp.Dummy("lambda"), sp.Dummy("phi")
dorder, dlambda, dphi = sp.Dummy("dorder"), sp.Dummy("dlambda"), sp.Dummy("dphi")
dg = StatUtils.buildErrorExpression(
    order*lambda_/sp.sin(phi/180*sp.pi),        # expression for g
    [                                           # symbol tuples
        (order, dorder),                        # (see doc of buildErrorExpression)
        (lambda_, dlambda),
        (phi, dphi)
    ]
).subs({                                        # substitute the values back
    order: 2, dorder: 0,
    lambda_: 589.6*10**-9, dlambda: 0.1*10**-9,
    phi: 50+9/60, dphi: 1/60
}) * units.m                                    # and readd the unit
del order, lambda_, phi, dorder, dlambda, dphi


if __name__ == "__main__":
    # load data as usual
    data = Table.Table(Parser.ParseGnuplot(open("rydberg.data", "r")))

    cols = map(data.__getitem__, ("order", "phi_1_deg", "phi_1_min",
        "phi_2_deg", "phi_2_min", "n2"))
    order = data["order"].symbol

    # convert the data to degree
    for prefix in ("phi_1_", "phi_2_"):
        symbolDeg = sp.Symbol(prefix + "deg")
        symbolMin = sp.Symbol(prefix + "min")
        symbolDest = sp.Symbol(prefix[:-1])
        data.derivate(
            symbolDest,
            ("deg", 1),
            symbolDeg + symbolMin
        )

    phi1 = data["phi_1"]
    phi2 = data["phi_2"]

    # join the two columns to get a statisical uncertainity from the
    # two measurements
    phi = sp.Symbol("phi")
    data.join(
        phi,
        [phi1, phi2],
        addError=1/60
    )

    # add the constant g
    g = data.add(Table.ConstColumn(
        sp.Symbol("g"),
        ("m", units.m),
        g,
        {
            StatisticalUncertainty: dg
        },
        len(data["phi"])
    )).symbol

    # calculate lambda from the previous values
    lambda_ = sp.Symbol("lambda")
    data.derivate(
        lambda_,
        ("nm", units.nm),
        g*sp.sin((phi / 180) * sp.pi) / order
    )

    # balmer series lambda from literature values
    balmer = sp.Symbol("lambda_balmer")
    n2 = data["n2"].symbol
    data.derivate(
        balmer,
        ("nm", units.nm),
        1/(units.rydberg*(1/4-1/(n2**2)))
    )

    # difference for those with valid n²
    difference = sp.Symbol("difference")
    data.derivate(
        difference,
        ("nm", units.nm),
        balmer - lambda_
    )

    # make the table update all columns in perfect™ order
    data.updateAll()
    SimplePrinter(
        ["phi", "lambda", "lambda_balmer", "difference"],
        [StatisticalUncertainty]
    )(data)
