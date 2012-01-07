# symbols_test.py - unit tests for symbols

"""This module provides unit tests for the ``pcc.symbols``
module.

As with all unit test modules, the tests it contains can be executed in many
ways, but most easily by going to the project root dir and executing
``python3 setup.py nosetests``.
"""

import unittest

import pcc.symbols as sy

class SymbolTester(unittest.TestCase):
    """Test harness for the ``pcc.symbols.Symbol`` class."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_symbol(self):
        """symbols.py: Test Symbol class"""

        a = sy.Symbol('a')
        b = sy.Symbol('b')
        a2 = sy.Symbol('a')

        self.assertEqual(a,a2)
        self.assertEqual(hash(a),hash(a2))
        self.assertNotEqual(a,b)
        self.assertNotEqual(hash(a),hash(b))

        self.assertFalse(a.terminal())
        
    def test_badname(self):
        """symbols.py: Test invalid symbol names"""

        with self.assertRaises(ValueError):
            a = sy.Symbol('_badname')

        with self.assertRaises(ValueError):
            a = sy.Symbol("")

class TokenTester(unittest.TestCase):
    """Test harness for the ``pcc.symbols.Token`` class."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_token(self):
        """symbols.py: Test Token class"""

        a = sy.Token('WORD',r'[a-zA-Z]+')
        b = sy.Token('NATURAL_NUMBER',r'[0-9]+')
        
        self.assertEqual(a.match("banana 42",0),"banana")
        self.assertEqual(b.match("banana 42",7),"42")

        self.assertTrue(a.terminal())

class SymbolStringTester(unittest.TestCase):
    """Test harness for the ``pcc.symbols.SymbolString`` class."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_sstring(self):
        """symbols.py: Test SymbolString class."""
        a = sy.Token('WORD',r'[a-zA-Z]+')
        b = sy.Token('NATURAL_NUMBER',r'[0-9]+')
        c = sy.Symbol('foo')

        d = sy.SymbolString( (a,c,b) )
        e = sy.SymbolString( (a,c,b) )
        f = sy.SymbolString( (c,c,b) )

        self.assertTrue( d == e )
        self.assertTrue( d[1:] == f[1:] )
        self.assertFalse( d == f )
        self.assertNotEqual( hash(d), hash(f) )
        for s in d:
            self.assertTrue( isinstance(s, sy.Symbol) )

        self.assertEqual(str(d),"WORD foo NATURAL_NUMBER")
        self.assertEqual(len(d), 3)
        self.assertTrue(e[0] in d)

