# encoding=utf-8
from __future__ import division, unicode_literals, print_function
from our_future import *

import abc
import itertools

import sympy as sp

class ValueClass(object):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self):
        raise TypeError("Thou shalt not instanciate this class")
        
    @staticmethod
    def getDefault(self):
        return None

class MeasuredValue(ValueClass):
    @staticmethod
    def getPropagationExpr(expr, variables, dvariables):
        return expr, False
    
    def __unicode__(self):
        return "measurement"

class MeanValue(MeasuredValue):
    def __unicode__(self):
        return "mean measurement"

class Uncertainity(ValueClass):
    @staticmethod
    def getPropagationExpr(expr, variables, dvariables):
        dexprs = [sp.diff(expr, variable) * dvariable for variable, dvariable in zip(variables, dvariables)]
        return sp.sqrt(sum(map(lambda x: x**2, dexprs))), True
        
    @staticmethod
    def getDefault(self):
        return 0
    
    def __unicode__(self):
        return "uncertainity"

class StatisticalUncertainity(ValueClass):
    def __unicode__(self):
        return "statistical uncertainity"

class SystematicalUncertainity(ValueClass):
    def __unicode__(self):
        return "systematical uncertainity"
