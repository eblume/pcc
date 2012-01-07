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

from pcc.parser import Parser, SYMBOL_REGEX, GrammarError, ParserSyntaxError

import itertools

class LLParser(Parser):
    
    def __init__(self,lexer):
        self.lexer = lexer
        self.finalized = False
        self.productions = {}
        self.start = None

    def addproduction(self,symbol,rule,action, start_production=False):
        # TODO - check for left-recursive and left-factored
        if self.finalized:
            raise GrammarError("Can't add a production after finalizing the "
                               "parser (maybe you called parse() too soon?")
        
        # Check to see if symbol is a valid symbol
        if not SYMBOL_REFEX.match(symbol):
            raise GrammarError('Invalid symbol name: {}'.format(symbol))

        # Check to see that the symbol isn't a token name
        if symbol in self.lexer.tokens:
            raise GrammarError('Symbol conflicts with Token name: {}'.format(
                               symbol))

        # Initial start_production check
        if self.start is not None and start_production:
            raise GrammarError('A Start production has already been specified.')

        # If rule is a string, split it
        if type(rule) == str:
            rule = rule.split()

        # Symbolize the rule
        rule_symbols = tuple([ self._make_symbol(x) for x in rule ])

        # Handle epsilon-productions:
        if len(rule_symbols == 0):
            rule_symbols = (self._make_symbol(''),)

        # Wrap up start_production stuff
        if start_production:
            rule_symbols += (_EOF,)
            self.start = (symbol,rule_symbols)

        # Add the final production to the production table
        
        if symbol not in self.productions:
            self.productions[symbol] = []

        self.productions[symbol].append(rule_symbols)

        # Also, add any new implicit symbols to the production table
        for implicit in rule_symbols:
            if not implicit.terminal and not implicit.name in self.productions:
                self.productions[implicit.name] = []


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
        
        # Initialize the (empty) FIRST and FOLLOW sets
        self.FIRST = {}
        self.FOLLOW = {}

        # Grammar error detection
        for symbol, rules in self.productions.items():
            # Detect the case that there are nonterminals without productions
            if len(rules) == 0:
                raise GrammarError('Symbol {} has no productions'.format(
                                   symbol))
            # LL(1) grammar rule dection
            if len(rules) > 1:
                for r1, r2 in itertools.combinations(rules,2):
                    if (
                         not self.first(r1).isdisjoint(self.first(r2)) or

                         (_EPSILON in self.first(r1) and not 
                            self.first(r2).isdisjoint(self.follow(symbol))) or

                         (_EPSILON in self.first(r2) and not
                            self.first(r1).isdisjoint(self.follow(symbol)))
                       ):
                        raise GrammarError("Grammar is not LL(1) - ambiguous "
                                           "derivation for symbol {}".format(
                                           symbol))


    def first(self,symbols):
        """Return the set of terminal symbols which belong to this string's
        FIRST set. See Aho, Ullman et.al.'s 2nd edition "Compilers...",
        section 4.4.2.
        
        `symbols` must be a hashable iterable (usually a tuple) of _RuleSymbol
        objects.

        The returned value will be a set of _RuleSymbol objects.
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
            if symbol.terminal:
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
                if (_EPSILON,) in rules:
                    result |= {_EPSILON}
                self.FIRST[symbols] = result
                return result
        else:
            # String of symbols (non-singleton)
            result = self._first_string(symbols)
            self.FIRST[symbols] = result
            return result

    def _first_string(self,symbols):
        "Helper func of ``first()`` on a string"
        result = set()
        flag_epsilon = True
        for symbol in symbols:
            new_set = self.first((symbol,))
            result |= (new_set - {_EPSILON} )
            if not _EPSILON in new_set:
                flag_epsilon = False
                break
        if flag_epsilon:
            result |= {_EPSILON}
        return result

    def follow(self,symbol):
        """Compute the FOLLOW set of a nonterminal symbol.

        `symbol` must be an instance of _RuleSymbol, and must be nonterminal.

        The result will be a set of terminal _RuleSymbol objects.
        """
        if not self.finalized: 
            self.finalize()

        if symbol.terminal:
            raise ValueError('Attempt to compute FOLLOW of a terminal')
        
        if symbol in self.FOLLOW:
            return self.FOLLOW[symbols]

        result = set()

        if symbol == self.start[0]:
            result |= {_EOF,}

        # Find productions with symbol on the RHS
        for nonterminal, rules in self.productions.items():
            for rule in rules:
                for index in range(len(rule)):
                    if not rule[index] == symbol:
                        continue

                    if index = len(rule) - 1:
                        # symbol occurs at the end of the rule
                        result |= self.follow(nonterminal)
                    else:
                        new_set = self.first(rule[index+1:])
                        result |= ( new_set - {_EPSILON} )
                        if _EPSILON in new_set:
                            result |= self.follow(nonterminal)

        # Check to make sure the set isn't empty, which is bad.
        if len(result) == 0:
            raise ValueError('FOLLOW set of {} is empty.'.format(symbol))

        # Final EPSILON check - shouldn't ever happen, but will spell
        # disaster if it does.
        if _EPSILON in result:
            raise ValueError('Somehow got EPSILON in the FOLLOW set of {}'
                             .format(symbol))

        self.FOLLOW[symbol] = result
        return result

    def parse(self,input):
        # TODO - remember to add _EOF as the last token after lexing is done.
        if not self.finalized:
            self.finalize()

    def _make_symbol(self,_name):
        """Helper function to symbolize the elements of a production's rule"""
        if name =="":
            return _EPSILON

        if len(name)==3 and name[0]=="'" and name[2]=="'":
            # String Literal!
            symbol = _RuleSymbol("LITERAL",True)
            symbol.literal = name[1]
            return symbol
    
        if name in self.lexer.tokens:
            return _RuleSymbol(name,True)

        # Otherwise, it's a non-terminal - check to make sure its name conforms
        if not SYMBOL_REGEX.match(name):
            raise GrammarError('Invalid implicit symbol name: {}'.format(
                               symbol))
        return _RuleSymbol(name,False)

class _RuleSymbol:
    """Wrapper class to reason about symbols that appear in productions"""
    def __init__(self,name,is_terminal):
        self.terminal = is_terminal
        self.name = name
        self.literal = None # Special field, just for string literals
    
    def __eq__(self,other):
        """Compare two ``_RuleSymbol`` objects for equivalence.

        >>> a = _RuleSymbol('foo',True)
        >>> b = _RuleSymbol('foo',True)
        >>> c = _RuleSymbol('bar',True)
        >>> d = _RuleSymbol('foo',False)
        >>> a == a
        True
        >>> a == b
        True
        >>> a is b
        False
        >>> a == c
        False
        >>> a == d
        False
        """
        return (
            self.terminal == other.terminal and
            self.name == other.name and
            self.literal == self.literal
        )

    def __hash__(self):
        """Hash a ``_RuleSymbol`` object to an integer value.
        
        >>> a = _RuleSymbol('foo',True)
        >>> b = _RuleSymbol('foo',True)
        >>> c = _RuleSymbol('bar',True)
        >>> hash(a) == hash(a)
        True
        >>> hash(a) == hash(b) # because a == b, this is supposed to be true
        True
        >>> hash(a) == hash(c)
        False
        """
        return hash((self.is_terminal,self.name,self.literal))

# shortcut symbols
# The names shouldn't ever cause conflicts, because they are not valid names
def _EPSILON = _RuleSymbol("",True)
def _EOF = _RuleSymbol("_",True)
    
