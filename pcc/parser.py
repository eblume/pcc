""" parser.py - CFG parsing with python functions as semantic actions

Create Parser objects, which take tokenized input (via lexer.py) and use
different parsing methods to synthesize BNF grammars in to productions with
semantic python actions. All semantic actions are python functions that take a
list as an argument (representing the values of sub-expressions) and return a
value as the result for that expression.
"""
# Copyright 2012 Erich Blume <blume.erich@gmail.com>
# ===========================
#
# This file is part of pcc
#
# pcc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# pcc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with pcc, in a file called COPYING.  If not, see
# <http://www.gnu.org/licenses/>.

from abc import ABCMeta,abstractmethod

def parser(lexer):
    """Create a Parser using the default algorithm."""
    # Only import from inside this function to avoid circular imports
    from pcc.ll import LLParser
    return LLParser(lexer)

class GrammarError(Exception):
    "Exception raised by a ``parser.Parser`` object *before* parsing begins."
    pass

class ParsingError(Exception):
    "Exception raised by a ``parser.Parser`` object when a syntax error occurs."
    pass

class Parser(metaclass=ABCMeta):
    """CFG parser of arbitrary BNF-like grammars.

    Actual implementations should subclass this abstract base class, and may
    have slightly different levels of 'computational power'. That is to say,
    an LL language is slightly less expressive than an SLR, which is less
    expressive than an LALR, which is less expressive than an LR language.
    All are essentially 'context free grammars'. If a parser encounters an
    error before parsing has begun (ie. an error with a production) then
    ``parser.GrammarError`` should be raised. If a parser encounters a syntax
    error during parsing, then ``parser.ParsingError`` should be raised.
    Other errors should be reported in the most reasonably expressive manner
    possible.
    """

    def ap(self,*args,**kwargs):
        """A shorthand for ``addproduction``."""
        self.addproduction(*args,**kwargs)

    @abstractmethod
    def addproduction(self):
        """Add a production (rule) to the grammar of the parser. Instructs the
        parser that `symbol` can be derived using `rule`, producing a result
        via `action`.

        See the documentation for the specific parser being used for further
        details.
        """
        raise NotImplementedError("Attempt to call an abstract method.")

    @abstractmethod
    def parse(self,input):
        """Parse the given `input` (a string) using the given rules and lexer.

        See the documentation for the specific parser being used for further
        details.
        """
        raise NotImplementedError("Attempt to call an abstract method.")

class SyntaxTree:
    """Abstract representation of the parse tree created by parsing input.

    The parser will create this object and return it as its result.

    This object is callable (like a function) with no arguments, which will
    return the result of processing the semantic actions of the parse tree.
    """

    def __init__(self,root):
        self.root = root

    def __call__(self):
        """Process the semantic actions of this parse tree."""
        return self.root.action()

class SyntaxNode:
    """Abstract representation of a single derivation when parsing input.

    `action` is the semantic action that will be executed by calling the
    ``action()`` method of this object. It may also be any non-collable value,
    in which case it will be treated as if the semantic action returned that
    value directly.

    `children` should be an iterable (usually a list or tuple) of SyntaxNode
    objects, or possibly None (indicating that there are no children). This
    will be stored in a tuple in a field called ``children`` on this node, which
    may be modified during optimization routines. If there are no children,
    this tuple will be empty.
    """

    def __init__(self,action,children=None):
        self._action = action
        if children:
            self.children = tuple(children)
        else:
            self.children = tuple()

    def action(self):
        if hasattr(self._action,'__call__'):
            return self._action([c.action() for c in self.children])
        else:
            return self._action


