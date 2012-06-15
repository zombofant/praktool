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
    def setUp(self):
        self.values = [1, 2, 3, 4, 5, 6]
        
    def test_skip(self):
        self.assertEqual([1, 1, 1, 1, 1], list(utils.diffNth(self.values, 1)))
        self.assertEqual([2, 2], list(utils.diffNth(self.values, 2)))

    def test_offset(self):
        self.assertEqual([1, 1, 1, 1], list(utils.diffNth(self.values, 1, offset=1)))
        self.assertEqual([2, 2], list(utils.diffNth(self.values, 2, offset=1)))
        self.assertEqual([2], list(utils.diffNth(self.values, 2, offset=2)))

class intNth(unittest.TestCase):
    def setUp(self):
        self.values = [1, 2, 3, 4, 5]
    
    def test_count(self):
        self.assertEqual(self.values, list(utils.intNth(self.values, 1)))
        self.assertEqual([3, 7], list(utils.intNth(self.values, 2)))
        self.assertEqual([6], list(utils.intNth(self.values, 3)))

    def test_offset(self):
        self.assertEqual(self.values[1:], list(utils.intNth(self.values, 1, offset=1)))
        self.assertEqual([5, 9], list(utils.intNth(self.values, 2, offset=1)))
        self.assertEqual([9], list(utils.intNth(self.values, 3, offset=1)))
