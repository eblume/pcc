# ll_test.py - unit tests for ll.py

"""This module provides unit tests for the ``pcc.ll``
module.

As with all unit test modules, the tests it contains can be executed in many
ways, but most easily by going to the project root dir and executing
``python3 setup.py nosetests``.
"""

import unittest

import pcc.ll as ll
from pcc.lexer import Lexer
from pcc.symbols import Symbol, SymbolString
import re

class LLTester(unittest.TestCase):
    """Test harness for ``pcc.ll.LLParser`` class.

    """

    def setUp(self):
        """Create the testing environment"""
        pass


    def tearDown(self):
        """Remove the testing environment"""
        pass

    def test_first(self):
        """ll.py: Test FIRST set creation"""
        # Grammar 4.28 in Aho, Ullman et al (except NUM instead of id)
        lexer = Lexer()
        lexer.addtoken(name='NUM',rule=r'[0-9]+')
        p = ll.LLParser(lexer)
        p.ap('E','T EP', lambda x: x[0] + x[1], start_production=True)
        p.ap('EP',"'+' T EP", lambda x: x[1] + x[2])
        p.ap('EP',"", lambda x: 0)
        p.ap('T',"F TP", lambda x: x[0] * x[1])
        p.ap('TP',"'*' F TP", lambda x: x[1] * x[2])
        p.ap('TP',"", lambda x: 1)
        p.ap('F',"'(' E ')'", lambda x: x[1])
        p.ap('F',"NUM", lambda x: int(x[0]))
        
        first_f = p.first(SymbolString((Symbol('F'),)))
        first_t = p.first(SymbolString((Symbol('T'),)))
        first_e = p.first(SymbolString((Symbol('E'),)))

        self.assertTrue(first_f == first_t == first_e)
        self.assertEqual(len(first_f),2)

        names = {t.name: t.rule.pattern for t in first_f}
        correct_names = {'LITERAL':'\\(', 'NUM':'[0-9]+'}
        self.assertEqual(names, correct_names)

        first_ep = p.first(SymbolString((Symbol('EP'),)))

        self.assertEqual(len(first_ep),2)
        
        names = {t.name: t.rule.pattern for t in first_ep}
        correct_names = {'LITERAL':'\\+', '_EPSILON': ''}
        self.assertEqual(names,correct_names)

        first_tp = p.first(SymbolString((Symbol('TP'),)))

        self.assertEqual(len(first_tp),2)

        names = {t.name: t.rule.pattern for t in first_tp}
        correct_names = {'LITERAL':'\\*', '_EPSILON': ''}
        self.assertEqual(names,correct_names)

    def test_follow(self):
        """ll.py: Test FOLLOW set creation"""
        # Grammar 4.28 in Aho, Ullman et al (except NUM instead of id)
        lexer = Lexer()
        lexer.addtoken(name='NUM',rule=r'[0-9]+')
        p = ll.LLParser(lexer)
        p.ap('E','T EP', lambda x: x[0] + x[1], start_production=True)
        p.ap('EP',"'+' T EP", lambda x: x[1] + x[2])
        p.ap('EP',"", lambda x: 0)
        p.ap('T',"F TP", lambda x: x[0] * x[1])
        p.ap('TP',"'*' F TP", lambda x: x[1] * x[2])
        p.ap('TP',"", lambda x: 1)
        p.ap('F',"'(' E ')'", lambda x: x[1])
        p.ap('F',"NUM", lambda x: int(x[0]))

        follow_e = p.follow(Symbol('E'))
        follow_ep = p.follow(Symbol('EP'))
        self.assertEqual(len(follow_e),2)
        self.assertEqual(follow_e,follow_ep)

        names = {t.name: t.rule.pattern for t in follow_e}
        correct_names = {'LITERAL':'\\)', '_EOF':"$"}
        self.assertEqual(names,correct_names)

        follow_t = p.follow(Symbol('T'))
        follow_tp = p.follow(Symbol('TP'))
        self.assertEqual(len(follow_t),3)
        self.assertEqual(follow_t,follow_tp)

        names = {t.rule.pattern: t.name for t in follow_t}
        correct_names = {'\\)':'LITERAL', '\\+':'LITERAL', "$":'_EOF'}
        self.assertEqual(names,correct_names)

        follow_f = p.follow(Symbol('F'))
        self.assertEqual(len(follow_f),4)
        
        names = {t.rule.pattern: t.name for t in follow_f}
        correct_names = {'\\*':'LITERAL', '\\)':'LITERAL', '\\+':'LITERAL',
                         "$":'_EOF'}
        self.assertEqual(names,correct_names)

    def test_grammar(self):
        """ll.py: Test a basic LL(1) grammar"""
        # Grammar 4.28 in Aho, Ullman et al (except NUM instead of id)
        lexer = Lexer()
        lexer.addtoken(name='NUM',rule=r'[0-9]+')
        p = ll.LLParser(lexer)
        p.ap('E','T EP', lambda x: x[0] + x[1], start_production=True)
        p.ap('EP',"'+' T EP", lambda x: x[1] + x[2])
        p.ap('EP',"", lambda x: 0)
        p.ap('T',"F TP", lambda x: x[0] * x[1])
        p.ap('TP',"'*' F TP", lambda x: x[1] * x[2])
        p.ap('TP',"", lambda x: 1)
        p.ap('F',"'(' E ')'", lambda x: x[1])
        p.ap('F',"NUM", lambda x: int(x[0]))
    
        self.assertEqual(p.parse("2+3*4"),14)
        self.assertEqual(p.parse("5"),5)
        self.assertEqual(p.parse("1+1+1+1+1+1+1"),7)
        
        

