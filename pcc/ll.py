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

from pcc.parser import Parser, GrammarError, ParsingError
from pcc.symbols import Symbol, Token, EOF, EPSILON, SymbolString, Lexeme

import itertools
import re

class LLParser(Parser):
    
    def __init__(self,lexer):
        self.lexer = lexer
        self.finalized = False
        self.productions = {}
        self.start = None
        self.terminals = {t for t in lexer.tokens.values()} | {EOF}

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
        rule_symbols=SymbolString([_make_symbol(self.lexer,x)
                                  for x in rule.split()])

        # Handle epsilon-productions:
        if len(rule_symbols) == 0:
            rule_symbols = SymbolString((EPSILON,))

        # Wrap up start_production stuff
        if start_production:
            rule_symbols += EOF
            self.start = (symbol,rule_symbols,action)

        # Add the final production to the production table
        if symbol not in self.productions:
            self.productions[symbol] = []
        self.productions[symbol].append((rule_symbols,action))

        # Add any new implicit symbols to the production table
        for implicit in rule_symbols:
            if ( not implicit.terminal() and
                 not implicit in self.productions
               ):
                self.productions[implicit] = []

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

        if self.first is None:
            raise GrammarError('At least one production must be marked as the '
                               'start production.')

        
        # Initialize the (empty) FIRST and FOLLOW caches
        self.FIRST = {}
        self.FOLLOW = {symbol: set() for symbol in self.productions}

        # Initialize the parsing table
        self.ptable = {symbol: {terminal: [] for terminal in self.terminals}
                       for symbol in self.productions}

        # Calculate the FOLLOW sets using the dynamic definition of FIRST sets
        # (Note that this MUST happen before we call self.follow, so it MUST
        #  happen before the grammar error detection routine)
        #
        # This uses Aho et.al.'s definition, in which empty sets are created,
        # the start symbol's FOLLOW is seeded with EOF, and then one loops over
        # the entire grammar indefinitely making corrections until the answer
        # (provably always) converges.
        self.FOLLOW[self.start[0]] |= {EOF}
        added_something_flag = True
        while added_something_flag:
            added_something_flag = False
            for symbol, rules in self.productions.items():
                for rule,action in rules:
                    # Special edge case - for the start production,
                    # trim off EOF here. The algorithm assumes EOF
                    # isn't part of a "sentential form".
                    if rule[len(rule)-1] == EOF:
                        rule = rule[:len(rule)-1]

                    for index in range(len(rule)):
                        rule_symbol = rule[index]
                        if rule_symbol.terminal():
                            continue
                        follow_set = self.FOLLOW[rule_symbol]
                        if index < len(rule)-1:
                            # "if there is more in this string
                            first_set = self.first(rule[index+1:])
                            added_something_flag |= _update_follow(
                                follow_set,first_set)
                            if EPSILON in first_set:
                                symbol_follow = self.FOLLOW[symbol]
                                added_something_flag |= _update_follow(
                                    follow_set,symbol_follow)
                        elif index == len(rule)-1:
                            # The last symbol in the rule
                            symbol_follow = self.FOLLOW[symbol]
                            added_something_flag |= _update_follow(
                                follow_set, symbol_follow)

        # Grammar error detection
        for symbol, rules in self.productions.items():
            # Detect the case that there are nonterminals without productions
            if len(rules) == 0:
                raise GrammarError('Symbol {} has no productions'.format(
                                   symbol.name))
            # LL(1) grammar rule dection
            elif len(rules) > 1:
                for (r1,_),(r2,_) in itertools.combinations(rules,2):
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
            for rule,action in rules:
                for term in self.first(rule): # either rule or symbol (GULP)
                    self.ptable[symbol][term].append((rule,action))
                if EPSILON in self.first(rule):
                    for term in self.follow(symbol):
                        self.ptable[symbol][term].append((rule,action))


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
                for rule,action in rules:
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
            new_set = self.first(SymbolString((symbol,)))
            result |= (new_set - {EPSILON} )
            if not EPSILON in new_set:
                flag_epsilon = False
                break
        if flag_epsilon:
            result |= {EPSILON}
        return result

    def follow(self,symbol):
        """Compute the FOLLOW set of a nonterminal symbol.

        Due to the constraint programming approach used to calculate the
        FOLLOW sets in this implementation, this function merely returns the
        pre-computed set - the actual set computation occurs in finalize()
        """
        if not self.finalized: 
            self.finalize()

        if symbol.terminal():
            raise ValueError('Attempt to compute FOLLOW of a terminal')
        
        return self.FOLLOW[symbol]

    def parse(self,input):
        """Use the recursive descent method to parse the input."""
        if not self.finalized:
            self.finalize()
        lexer = _LexemeIterator(self.lexer,input)
        start_symbol, start_rule, start_action = self.start
        return _rd_parse_rule(start_rule,start_action,lexer,self.ptable)
        
def _make_symbol(lexer,name):
    """Helper function to symbolize the elements of a production's rule"""

    # If it looks like a string literal, make a literal-like token
    if len(name)==3 and name[0]=="'" and name[2]=="'":
        # A quick reminder here that this token is NOT the same as
        # the token called "LITERAL" that is generated automatically by the
        # lexer when report_literals is True. This is a sort of Token Template,
        # and if we get a Lexeme with the lexer's LITERAL token, we check to
        # see if the matched lexeme text matche's this character.
        return Token("LITERAL",re.escape(name[1]))

    # If the name is in the lexer's token set, use that token
    if name in lexer.tokens:
        return lexer.tokens[name]

    # Otherwise, we assume it's a Symbol. If it's not, then the Symbol
    # regexp should catch it and barf, which is what we want.
    return Symbol(name)

def _rd_parse_rule(rule,action,lexer,parse_table):
    """Recursive function to parse the input"""
    input_values = []
    for symbol in rule:
        if symbol.terminal():

            if symbol == EPSILON:
                # epsilon-production - treat like input, but consume nothing
                input_values.append(None)
                continue
            
            next = lexer.poll()
    
            # if the wrong token is lexed:
            if ( next.token != symbol or
                 (symbol.name == "LITERAL" and not symbol.match(next.match,0))
               ):
                raise ParsingError('Expected {} but found {} on line {} at '
                    'position {}'.format( symbol.name, next.token.name,
                    next.line, next.position))
            
            input_values.append(next.match)
            continue
        else:
            #non-terminal symbol
            # find the right derivation to follow
            next = lexer.peek()
            productions = parse_table[symbol][next.token]
            
            if len(productions) == 0:
                raise ParsingError('Unexpected input "{}" on line {} at '
                    'position {}'.format(next.match,next.line,next.position))
            elif len(productions) > 1:
                # TODO - more than one production means this isn't actually
                # LL(1). In the future, we should automatically left-factor
                # and eliminate recursion when possible, in which case this
                # condition would be a definite error. However instead,
                # we will simply choose the first production, but this is
                # a BUG and should be fixed.
                pass
            new_rule,new_action = productions[0]
            # RECURSION
            input_values.append(_rd_parse_rule(new_rule,new_action,lexer,
                                parse_table))
            continue
    # Parsing complete, now perform the 'action'
    if hasattr(action, '__call__'):
        return action(input_values)
    else:
        return action

    
class _LexemeIterator:
    """Helper class to handle reading values from the ``Lexer``."""

    def __init__(self,lexer,input):
        self.n = lexer.lex(input)
        self.next_symbol = None
        self.scan()

    def scan(self):
        "Load the next lexeme"
        try:
            self.next_symbol = next(self.n)
        except StopIteration:
            def _false_iter():
                while True:
                    yield Lexeme(EOF,"EOF",-1,-1)
            self.n = _false_iter()
            self.next_symbol = next(self.n)

    def peek(self):
        """Return the next lexeme, but do not remove it from the input."""
        return self.next_symbol

    def poll(self):
        """Return and remove the next lexeme from the input."""
        result = self.next_symbol
        self.scan()
        return result

def _update_follow(a,b):
    "Add new elements EXCEPT EPSILON from b to a. Return True if not no-op."
    b = b - {EPSILON}
    if b - a:
        a |= b
        return True
    return False
                        


