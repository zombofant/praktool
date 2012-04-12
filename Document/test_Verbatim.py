from __future__ import division, print_function, unicode_literals
from our_future import *

import unittest

import Verbatim

class Parser(unittest.TestCase):
    def test_simple(self):
        simple = r"""\documentclass{<? "scrartcl" ?>}"""
        
        self.assertEqual(
            list(Verbatim.Parser([simple])),
            [
                Verbatim.SectionLiteral(r"""\documentclass{"""),
                Verbatim.SectionPython(" \"scrartcl\" "),
                Verbatim.SectionLiteral(r"""}""")
            ]
        )

    def test_escape(self):
        escape = r"""\documentclass{scrartcl}
\<?"""

        self.assertEqual(
            list(Verbatim.Parser([escape])),
            [
                Verbatim.SectionLiteral(r"""\documentclass{scrartcl}
<?"""),
            ]
        )

    def test_multiescape(self):
        multi = r"""\documentclass{\\<?}"""

        self.assertEqual(
            list(Verbatim.Parser([multi])),
            [
                Verbatim.SectionLiteral(r"""\documentclass{\<?}""")
            ]
        )

    def test_syntaxError(self):
        errornous = r"""<?
for x:
    print("foo") ?>"""
        self.assertRaises(SyntaxError, list, Verbatim.Parser([errornous]))

    def test_indentFix(self):
        indented = r"""<?
        print("meow")
        ?><?
                for x in xrange(10):
                    "foo"
                ?>"""

        self.assertEqual(
            list(Verbatim.Parser([indented])),
            [
                Verbatim.SectionPython(r"""print("meow")"""),
                Verbatim.SectionPython("""for x in xrange(10):
    "foo"
""")
            ]
        )
