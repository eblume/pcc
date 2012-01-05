# lexer_test.py - unit tests for lexer.py

"""This module provides unit tests for the ``facade.lexer``
module.

As with all unit test modules, the tests it contains can be executed in many
ways, but most easily by going to the project root dir and executing
``python3 setup.py nosetests``.
"""

import unittest

import pcc.lexer as fl

class LexerTester(unittest.TestCase):
    """Test harness for ``facade.lexer.Lexer`` class.

    """

    def setUp(self):
        """Create the testing environment"""
        pass

    def tearDown(self):
        """Remove the testing environment"""
        pass

    def test_SimpleTokens(self):
        """lexer.py: Test a simple lexicon"""
        l = fl.Lexer()
        l.addtoken('WORD',r'[a-zA-Z]+')
        l.addtoken('NUMBER',r'[0-9]+')

        input = """
        this is
        a
        tes42t
        """

        tokens = [t for t in l.lex(input)]
        
        self.assertEqual(len(tokens),6)
        self.assertEqual(tokens[4].match,"42")

    def test_greedy(self):
        """lexer.py: Test greedy matching"""
        l = fl.Lexer()
        l.addtoken('ONE',r'\*')
        l.addtoken('TWO',r'\*\*')

        tokens = [t for t in l.lex(" * ")]
        self.assertEqual(len(tokens),1)
        self.assertEqual(tokens[0].name,"ONE")

        tokens = [t for t in l.lex(" ** ")]
        self.assertEqual(len(tokens),1)
        self.assertEqual(tokens[0].name,"TWO")
