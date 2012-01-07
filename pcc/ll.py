"""ll.py - Implementation of an LL(1) (Left to right Leftmost) parser generator
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

from pcc.parser import Parser, GrammarError, ParserSyntaxError
from pcc.symbols import Symbol, Token, EOF, EPSILON, SymbolString

import itertools

class LLParser(Parser):
    
    def __init__(self,lexer):
        self.lexer = lexer
        self.finalized = False
        self.productions = {}
        self.start = None
        self.terminals = {t for t in lexer.tokens.values()} + {EOF}

    def addproduction(self,symbol,rule,action, start_production=False):
        if self.finalized:
            raise ValueError("Can't add a production after finalizing the "
                             "parser (maybe you called parse() too soon?")

        symbol = Symbol(symbol)

        if symbol.name in self.lexer.tokens:
            raise GrammarError('Symbol conflicts with Token name: {}'.format(
                               symbol.name))

        # Initial start_production check
        if self.start is not None and start_production:
            raise GrammarError('A Start production has already been specified.')

        # Symbolize the rule
        rule_string=SymbolString([self._make_symbol(x) for x in rule.split()])

        # Handle epsilon-productions:
        if len(rule_symbols == 0):
            rule_symbols = SymbolString((EPSILON,))

        # Wrap up start_production stuff
        if start_production:
            self.start = (symbol,rule_symbols)

        # Add the final production to the production table
        if symbol not in self.productions:
            self.productions[symbol] = []
        self.productions[symbol].append(rule_symbols)

        # Add any new implicit symbols to the production table
        for implicit in rule_symbols:
            if ( not implicit.terminal() and
                 not implicit.name in self.productions
               ):
                self.productions[implicit.name] = []

        # Add any new string literal tokens to the terminals set
        self.terminals |= { s for s in rule_symbols if s.terminal() }


    def finalize(self):
        """This function actually performs the 'parser generation' that gives
        ``pcc`` its name (compiler compiling). Callable only once, it constructs
        the FIRST and FOLLOW sets, the parsing table, the action table, etc.
        
        In general terms, it prepares the parser to be able to call 'parse'.
        """
        # TODO - after this is called, the object should also be serializible.
        #        In the future, a finalized parser should support being written
        #        to (and read from) disk.

        if self.finalized:
            raise ValueError('Attempt to finalize an already finalized parser.')
        self.finalized = True
        
        # Initialize the (empty) FIRST and FOLLOW caches
        self.FIRST = {}
        self.FOLLOW = {}

        # Initialize the parsing table
        self.ptable = {x: {y: [] for y in self.terminals}
                       for x in self.productions}

        # Grammar error detection
        for symbol, rules in self.productions.items():
            # Detect the case that there are nonterminals without productions
            if len(rules) == 0:
                raise GrammarError('Symbol {} has no productions'.format(
                                   symbol.name))
            # LL(1) grammar rule dection
            elif len(rules) > 1:
                for r1, r2 in itertools.combinations(rules,2):
                    if (
                         not self.first(r1).isdisjoint(self.first(r2)) or

                         (EPSILON in self.first(r1) and not 
                            self.first(r2).isdisjoint(self.follow(symbol))) or

                         (EPSILON in self.first(r2) and not
                            self.first(r1).isdisjoint(self.follow(symbol)))
                       ):
                        raise GrammarError("Grammar is not LL(1) - ambiguous "
                                           "derivation for symbol {}".format(
                                           symbol.name))

        # construct the parsing table
        for symbol, rules in self.productions.items():
            for rule in rules:
                for term in self.first(rule): # either rule or symbol (GULP)
                    self.ptable[symbol][term].append((symbol,rule))
                if EPSILON in self.first(rule):
                    for term in self.follow(symbol):
                        self.ptable[symbol][term].append((symbol,rule))


    def first(self,symbols):
        """Return the set of terminal ``Symbol``s which belong to this string's
        FIRST set. See Aho, Ullman et.al.'s 2nd edition "Compilers...",
        section 4.4.2.
        
        `symbols` must be a ``pcc.symbols.SymbolString`` object.

        The returned value will be a set of terminal``Symbol`` objects.
        """
        # First, finalize (end rule-adding phase)
        if not self.finalized:
            self.finalize()

        # Dynamic return to cut down execution time
        if symbols in self.FIRST:
            return self.FIRST[symbols]

        # Actual definition:

        if len(symbols) == 1:
            symbol = symbols[0]
            if symbol.terminal():
                # Terminal singletons are their own FIRST set
                result = { symbol }
                self.FIRST[symbols] = result
                return result
            else: 
                # Non-terminal singletons use the FIRST of every rule they
                # produce
                rules = self.productions[symbol]
                result = set()
                for rule in rules:
                    result |= self._first_string(rule)
                if SymbolString((EPSILON,)) in rules:
                    result |= {EPSILON}
                self.FIRST[symbols] = result
                return result
        else:
            # String of symbols (non-singleton)
            result = self._first_string(symbols)
            self.FIRST[symbols] = result
            return result

    def _first_string(self,symbols):
        "Helper func of ``first()`` on a SymbolString"
        result = set()
        flag_epsilon = True
        for symbol in symbols:
            new_set = self.first(SymbolString(symbol,)))
            result |= (new_set - {EPSILON} )
            if not EPSILON in new_set:
                flag_epsilon = False
                break
        if flag_epsilon:
            result |= {EPSILON}
        return result

    def follow(self,symbol):
        """Compute the FOLLOW set of a nonterminal symbol.

        `symbol` must be an instance of _RuleSymbol, and must be nonterminal.

        The result will be a set of terminal _RuleSymbol objects.
        """
        if not self.finalized: 
            self.finalize()

        if symbol.terminal():
            raise ValueError('Attempt to compute FOLLOW of a terminal')
        
        if symbol in self.FOLLOW:
            return self.FOLLOW[symbol]

        result = set()

        if symbol == self.start[0]:
            # This is the start symbol, so it's FOLLOW will always have EOF
            result |= {EOF}

        # Find productions with symbol on the RHS
        for nonterminal, rules in self.productions.items():
            for rule in rules:
                for index in range(len(rule)):
                    if not rule[index] == symbol:
                        continue

                    if index == len(rule) - 1:
                        # symbol occurs at the end of the rule
                        result |= self.follow(nonterminal)
                    else:
                        new_set = self.first(rule[index+1:])
                        result |= ( new_set - {EPSILON} )
                        if EPSILON in new_set:
                            result |= self.follow(nonterminal)

        # Check to make sure the set isn't empty, which is bad.
        if len(result) == 0:
            raise ValueError('FOLLOW set of {} is empty.'.format(symbol))

        # Final EPSILON check - shouldn't ever happen, but will spell
        # disaster if it does.
        if EPSILON in result:
            raise ValueError('Somehow got EPSILON in the FOLLOW set of {}'
                             .format(symbol.name))

        self.FOLLOW[symbol] = result
        return result

    def parse(self,input):
        # TODO - remember to add _EOF as the last token after lexing is done.
        if not self.finalized:
            self.finalize()

    def _make_symbol(self,name):
        """Helper function to symbolize the elements of a production's rule"""

        # If it looks like a string literal, make a literal-like token
        if len(name)==3 and name[0]=="'" and name[2]=="'":
            return Token("LITERAL",name[1])
    
        # If the name is in the lexer's token set, use that token
        if name in self.lexer.tokens:
            return self.lexer.tokens[name]

        # Otherwise, we assume it's a Symbol. If it's not, then the Symbol
        # regexp should catch it and barf, which is what we want.
        return Symbol(name)

    
