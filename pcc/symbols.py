"""symbols.py - Helper classes for grammar symbols, sentences, tokens, etc.
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

import re
import itertools

SYMBOL_MATCH_RULE = r'[a-z][_a-z]*'
TOKEN_MATCH_RULE = r'[A-Z][_A-Z]*'

class Symbol:
    """Terminal or nonterminal member of a grammar.

    By default, objects instantiated from Symbol will return ``False`` when
    queried by ``Symbol.terminal`` - subclasses may implement other
    behavior as needed.

    `name` may be anything that matches ``SYMBOL_MATCH_RULE``, a string that
    is used as a regular expression by this module. By default, this is any
    series of **lowercase** letters and underscores that starts with a single
    lowercase letter.
    """

    def __init__(self,name):
        if not re.match(SYMBOL_MATCH_RULE,name):
            raise ValueError('Invalid Symbol name: {}'.format(name))
        self.name = name

    def __str__(self):
        return self.name

    def terminal(self):
        return False

    def __hash__(self):
        return hash(self.name)

    def __eq__(self,other):
        return type(self) == type(other) and self.name == other.name

class Token(Symbol):
    """Terminal Symbol

    `name` must be anything that matches ``TOKEN_MATCH_RULE``, a string that
    is used as a regular expression by this module. By default, this is any
    series of **uppercase** letters and underscores that starts with a single
    uppercase letter.

    `rule` is a string that will be used as a regular expression to lex input
    by ``pcc.lexer``. To avoid lexing issues, use only basic regular expression
    operations - avoid backreferences, unnecessary grouping, or the input
    boundary markers (^ and $). Lexing may still work with these, but your
    mileage will vary.

    `silent`, if True, will tell lexers to supress generating this token. Input
    will still be consumed, but no token will be sent to the caller. This is
    primarily useful for ignore whitespace, comments, etc.

    There are two special ``Token``s that do not follow normal naming rules
    (their names start with an underscore) in this module: ``EOF`` and
    ``EPSILON``. ``EPSILON`` can be used for 'empty' productions, and ``EOF``
    can be used to represent the end of the stream. Do not use either of these
    special tokens in lexing - they will produce undefined results.
    """

    def __init__(self, name, rule, silent = False):
        if not re.match(TOKEN_MATCH_RULE,name):
            raise ValueError("Invalid Token name: {}".format(name))
        self.name = name
        self.rule = re.compile(rule)
        self.silent = silent

    def terminal(self):
        return True

    def match(self,input,position):
        """Returns a string matched from ``input[position:]``, or None."""
        m = self.rule.match(input,position)
        return m.group(0) if m else None

    def __hash__(self):
        return hash((super().__hash__(),self.rule,self.silent))

    def __eq__(self,other):
        return ( type(self) == type(other) and
                 super().__eq__(other) and self.rule == other.rule and
                 self.silent == other.silent
               )

    def __repr__(self):
        return "<pcc.symbols.Token({},r'{}')>".format(
                self.name,self.rule.pattern)

class SymbolString:
    """An ordered collection of ``Symbol`` objects.

    Immutable, hashable, iterable, sliceable, etc. Works like strings.
    """

    def __init__(self,symbols):
        self._symbols = tuple(symbols)

    def __iter__(self):
        for s in self._symbols:
            yield s

    def __hash__(self):
        return hash(self._symbols)

    def __eq__(self, other):
        return type(self) == type(other) and self._symbols == other._symbols
    
    def __len__(self):
        return len(self._symbols)

    def __getitem__(self,index):
        try:
            # Assume index is a n integer
            return next(itertools.islice(self._symbols,index,index+1))
        except TypeError:
            # Assume index is a slice object
            return SymbolString(list(itertools.islice(
                            self._symbols,index.start,index.stop,index.step)))

    def __contains__(self,item):
        return item in self._symbols

    def __str__(self):
        return " ".join(str(x) for x in self._symbols)

    def __add__(self, elem):
        new_symbols = list(self._symbols)
        new_symbols.append(elem)
        return SymbolString(new_symbols)


class Lexeme:
    """Input (string) that has been matched to some ``Token``.

    Every ``Lexeme`` object has the fields ``token``, ``match``, ``line``, and
    ``position``.
    """
    def __init__(self, token, match, line, position):
        self.token = token
        self.match = match
        self.line = line
        self.position = position


EPSILON = Token("FAKE",r"")
EPSILON.name = "_EPSILON"
EPSILON.__doc__ = "Special ``Token`` to represent an empty string for grammars"
EOF = Token("FAKE",r"$")
EOF.name = "_EOF"
EOF.__doc__ = "Special ``Token`` to represent the end of the input."

