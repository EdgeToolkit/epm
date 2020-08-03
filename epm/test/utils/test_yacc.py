import os
import unittest

from epm.test.helpers import DATA_DIR
from epm.utils.yacc.condition import Yacc as ConditionYacc


class TestCondition(unittest.TestCase):
    VARS ={'os': 'Windows',
           'compiler': 'Visual Studio',
           'compiler.version': 16,
           }

    yacc = ConditionYacc(VARS)

    def test_basic(self):
        self.assertTrue(self.yacc.parse('os==Windows'))
        self.assertTrue(self.yacc.parse('os == Windows'))
        self.assertFalse(self.yacc.parse('os == Linux'))
        self.assertFalse(self.yacc.parse('not.exist.field == Linux'))
        self.assertTrue(self.yacc.parse('not.exist.field != Linux'))
        self.assertTrue(self.yacc.parse('not.exist.field == None'))

        self.assertTrue(self.yacc.parse("compiler == 'Visual Studio'"))
        self.assertTrue(self.yacc.parse('compiler == "Visual Studio"'))
        self.assertFalse(self.yacc.parse('compiler != "Visual Studio"'))
        self.assertTrue(self.yacc.parse('compiler == "Visual Studio" && os == Windows'))

        self.assertFalse(self.yacc.parse('compiler == "Visual Studio" && os == Linux'))
        self.assertTrue(self.yacc.parse('compiler == "Visual Studio" || os == Linux'))

    def test_error(self):

        from epm.errors import ESyntaxError
        self.assertRaises(ESyntaxError, self.yacc.parse,
                          'compiler == "Visual Studio" or os == Linux')


