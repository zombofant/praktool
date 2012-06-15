# encoding=utf-8
from __future__ import division, unicode_literals, print_function
from our_future import *

import abc
import itertools

import sympy as sp

class Uncertainty(object):
    @staticmethod
    def getDefault():
        return 0
    
    def __unicode__(self):
        return "uncertainity"

class StatisticalUncertainty(Uncertainty):
    def __unicode__(self):
        return "statistical uncertainity"

class SystematicalUncertainty(Uncertainty):
    def __unicode__(self):
        return "systematical uncertainity"
