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
from pcc.symbols import Symbol, SymbolString, Token
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
        p.ap('e','t ep', lambda x: x[0] + x[1], start_production=True)
        p.ap('ep',"'+' t ep", lambda x: x[1] + x[2])
        p.ap('ep',"", lambda x: 0)
        p.ap('t',"f tp", lambda x: x[0] * x[1])
        p.ap('tp',"'*' f tp", lambda x: x[1] * x[2])
        p.ap('tp',"", lambda x: 1)
        p.ap('f',"'(' e ')'", lambda x: x[1])
        p.ap('f',"NUM", lambda x: int(x[0]))
        
        first_f = p.first(SymbolString((Symbol('f'),)))
        first_t = p.first(SymbolString((Symbol('t'),)))
        first_e = p.first(SymbolString((Symbol('e'),)))

        self.assertTrue(first_f == first_t == first_e)
        self.assertEqual(len(first_f),2)

        names = {t.name: t.rule.pattern for t in first_f}
        correct_names = {'LITERAL':'\\(', 'NUM':'[0-9]+'}
        self.assertEqual(names, correct_names)

        first_ep = p.first(SymbolString((Symbol('ep'),)))

        self.assertEqual(len(first_ep),2)
        
        names = {t.name: t.rule.pattern for t in first_ep}
        correct_names = {'LITERAL':'\\+', '_EPSILON': ''}
        self.assertEqual(names,correct_names)

        first_tp = p.first(SymbolString((Symbol('tp'),)))

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
        p.ap('e','t ep', lambda x: x[0] + x[1], start_production=True)
        p.ap('ep',"'+' t ep", lambda x: x[1] + x[2])
        p.ap('ep',"", lambda x: 0)
        p.ap('t',"f tp", lambda x: x[0] * x[1])
        p.ap('tp',"'*' f tp", lambda x: x[1] * x[2])
        p.ap('tp',"", lambda x: 1)
        p.ap('f',"'(' e ')'", lambda x: x[1])
        p.ap('f',"NUM", lambda x: int(x[0]))

        follow_e = p.follow(Symbol('e'))
        follow_ep = p.follow(Symbol('ep'))
        self.assertEqual(len(follow_e),2)
        self.assertEqual(follow_e,follow_ep)

        names = {t.name: t.rule.pattern for t in follow_e}
        correct_names = {'LITERAL':'\\)', '_EOF':"$"}
        self.assertEqual(names,correct_names)

        follow_t = p.follow(Symbol('t'))
        follow_tp = p.follow(Symbol('tp'))
        self.assertEqual(len(follow_t),3)
        self.assertEqual(follow_t,follow_tp)

        names = {t.rule.pattern: t.name for t in follow_t}
        correct_names = {'\\)':'LITERAL', '\\+':'LITERAL', "$":'_EOF'}
        self.assertEqual(names,correct_names)

        follow_f = p.follow(Symbol('f'))
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
        p.ap('e','t ep', lambda x: x[0] + x[1], start_production=True)
        p.ap('ep',"'+' t ep", lambda x: x[1] + x[2])
        p.ap('ep',"", lambda x: 0)
        p.ap('t',"f tp", lambda x: x[0] * x[1])
        p.ap('tp',"'*' f tp", lambda x: x[1] * x[2])
        p.ap('tp',"", lambda x: 1)
        p.ap('f',"'(' e ')'", lambda x: x[1])
        p.ap('f',"NUM", lambda x: int(x[0]))
    
        self.assertEqual(p.parse("2+3*4"),14)
        self.assertEqual(p.parse("5"),5)
        self.assertEqual(p.parse("1+1+1+1+1+1+1"),7)
        self.assertEqual(p.parse("(5+2)"),7)
        self.assertEqual(p.parse("1+((((((((((3))))))))))"),4)
        
    def test_symbolize(self):
        """ll.py: Test converting a rule string in to a SymbolString"""

        # SKIP FOR NOW
        return
        
        lexer = Lexer()
        lexer.addtoken(name='NUM',rule=r'[0-9]+')
        p = ll.LLParser(lexer)

        s_string = p.symbolize("a b c d")
        self.assertEqual(len(s_string),4)
        for symbol in s_string:
            self.assertTrue(isinstance(symbol,Symbol))
            self.assertFalse(isinstance(symbol,Token))
            self.assertFalse(symbol.terminal())

        s_string = p.symbolize("NUM NUM NUM")
        self.assertEqual(len(s_string),3)
        for symbol in s_string:
            self.assertTrue(isinstance(symbol,Symbol))
            self.assertTrue(isinstance(symbol,Token))
            self.assertTrue(symbol.terminal())
            self.assertEqual(symbol,Token("NUM",r'[0-9]+'))

        s_string = p.symbolize(" '(~''' NUM '~)''' ")
        self.assertEqual(len(s_string),3)
        self.assertTrue(isinstance(s_string[0]),Token)
        match_str = s_string[0].match("(~''")
        self.assertEqual(len(match_str),4)
        

