# lexer_test.py - unit tests for lexer.py

"""This module provides unit tests for the ``pcc.lexer``
module.

As with all unit test modules, the tests it contains can be executed in many
ways, but most easily by going to the project root dir and executing
``python3 setup.py nosetests``.
"""

import unittest

import pcc.lexer as fl

class LexerTester(unittest.TestCase):
    """Test harness for ``pcc.lexer.Lexer`` class.

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
        l.addtoken(name='WORD',rule=r'[a-zA-Z]+')
        l.addtoken(name='NUMBER',rule=r'[0-9]+')

        input = """
        this is
        a
        tes42t
        """

        lexemes = [t for t in l.lex(input)]
        
        #self.assertEqual(len(lexemes),6)
        self.assertEqual(lexemes[4].match,"42")

    def test_ignorenewlines(self):
        """lexer.py: Test ignoring newlines"""
        l = fl.Lexer(ignore_whitespace=False)
        l.addtoken(name='WORD',rule=r'[a-zA-Z]+')
        l.addtoken(name="SPACE",rule=r' ')

        input = "one\n two three\n four\n \nfive \n"
        
        lexemes = [t for t in l.lex(input)]
    
        self.assertTrue(len(lexemes)==10)
        self.assertEqual(lexemes[5].match," ")

    def test_greedy(self):
        """lexer.py: Test greedy matching"""
        l = fl.Lexer()
        l.addtoken(name='ONE',rule=r'\*')
        l.addtoken(name='TWO',rule=r'\*\*')

        lexemes = [t for t in l.lex(" * ")]
        self.assertEqual(len(lexemes),1)
        self.assertEqual(lexemes[0].token.name,"ONE")

        lexemes = [t for t in l.lex(" ** ")]
        self.assertEqual(len(lexemes),1)
        self.assertEqual(lexemes[0].token.name,"TWO")

