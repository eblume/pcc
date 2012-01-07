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

SYMBOL_MATCH_RULE = r'[a-zA-Z][_a-zA-Z0-9]*'
_SYMBOL_REGEXP = re.compile(SYMBOL_MATCH_RULE)

class Symbol:
    """Terminal or nonterminal member of a grammar.

    By default, objects instantiated from Symbol will return ``False`` when
    queried by ``Symbol.terminal`` - subclasses may implement other
    behavior as needed.

    `name` may be anything that matches ``SYMBOL_MATCH_RULE``, a string that
    is used as a regular expression by this module.
    """

    def __init__(self,name):
        if not _SYMBOL_REGEXP.match(name):
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
        super().__init__(name)
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

EPSILON = Token("fake",r"")
EPSILON.name = "_EPSILON"
EPSILON.__doc__ = "Special ``Token`` to represent an empty string for grammars"
EOF = Token("fake",r"$")
EOF.name = "_EOF"
EOF.__doc__ = "Special ``Token`` to represent the end of the input."

class SymbolString:
    """An ordered collection of ``Symbol`` objects.

    Immutable, hashable, iterable, sliceable, etc. Works like strings.
    """

    def __init__(self,symbols):
        self._symbols = list(symbols)

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
            return list(itertools.islice(self._symbols,index.start,index.stop,
                                         index.step))

    def __contains__(self,item):
        return item in self._symbols

    def __str__(self):
        return " ".join(str(x) for x in self._symbols)

    def __add__(self, elem):
        new_symbols = list(self._symbols)
        new_symbols.append(elem)
        return SymbolString(new_symbols)


