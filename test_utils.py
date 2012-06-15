from __future__ import unicode_literals, print_function, division
from our_future import *

import unittest

import utils

class empty(unittest.TestCase):
    def test_empty(self):
        iterable = []
        self.assertTrue(utils.empty(iterable))

    def test_nonEmpty(self):
        iterable = [1]
        self.assertFalse(utils.empty(iterable))

    def test_error(self):
        nonIterable = 10
        self.assertRaises(TypeError, utils.empty, nonIterable)

class diffNth(unittest.TestCase):
    def test_one(self):
        values = [1, 2, 3, 4, 5]
        self.assertEqual([1, 1, 1, 1], list(utils.diffNth(values, 1)))

    def test_two(self):
        values = [1, 2, 3, 4, 5]
        self.assertEqual([2, 2], list(utils.diffNth(values, 2)))

class intNth(unittest.TestCase):
    def test_one(self):
        values = [1, 2, 3, 4, 5]
        self.assertEqual([1, 2, 3, 4, 5], list(utils.intNth(values, 1)))
        
    def test_two(self):
        values = [1, 2, 3, 4, 5]
        self.assertEqual([3, 7], list(utils.intNth(values, 2)))
        
    def test_three(self):
        values = [1, 2, 3, 4, 5]
        self.assertEqual([6], list(utils.intNth(values, 3)))

