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

from pcc.parser import (Parser, GrammarError, ParsingError, SyntaxTree,
                        SyntaxNode)
from pcc.symbols import (Symbol, Token, EOF, EPSILON, SymbolString, Lexeme,
                         SYMBOL_MATCH_RULE, TOKEN_MATCH_RULE)
from pcc.stringtools import unique_string

import itertools
import re

class LLParser(Parser):
    
    def __init__(self,lexer):
        self.lexer = lexer
        self.finalized = False
        self.productions = {}
        self.start = None
        self.literals = {}
        self.terminals = {t for t in lexer.tokens.values()} | {EOF}

    def addproduction(self,symbol,rule,action=None,start_production=False):
        """Add a production to generate `symbol` using `rule`.

        For convenience, `symbol` is a string which will be the name of the
        symbol being derived with this production, and `rule` is simply a
        string in a form similar to BNF form that shows the decleration of the
        production. See ``LLParser.symbolize()`` for more information on `rule`.

        `action` is any function which takes one list-type argument and
        returns either None or a single value. This is the *semantic action*
        for this production. The argument is a list, each element being the
        value returned by the semantic action of the produciton generating that
        element's corresponding part of the rule. In the case of terminal
        symbols, the exact input matched will be used in the argument. Also,
        action may be any other sort of value (including None), in which case
        that value will be used for upper-level derivations.

        It is common for `action` to be a lambda expression for simple
        grammars, but any sort of function may be used.

        `start_production` flags this production as being the one and only
        (and necessary) production that caps the parse tree. You must, before
        parsing, declare exactly one `start_production`. If your grammar has
        multiple 'top-level' productions, simply define a new start production
        that can be derived from any of your 'top-level' productions.
        """
        if self.finalized:
            raise ValueError("Can't add a production after finalizing the "
                             "parser (maybe you called parse() too soon?")

        symbol = Symbol(symbol)

        # Initial start_production check
        if self.start is not None and start_production:
            raise GrammarError('A Start production has already been specified.')

        # Symbolize the rule
        rule_symbols = self.symbolize(rule)

        # Wrap up start_production stuff
        if start_production:
            self.start = (symbol,rule_symbols+EOF,action)

        # Add the final production to the production table
        if symbol not in self.productions:
            self.productions[symbol] = []
        self.productions[symbol].append((rule_symbols,action))

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

        # Initialize the FIRST and FOLLOW sets, as well as the parse table
        self.initialize_sets()

        # Grammar error detection
        self.error_check()

        # construct the parsing table
        self.construct_ptable()

    def initialize_sets(self):
        """Construct the FIRST and FOLLOW sets, and initialize the parse table.

        This function finalizes the parser if it has not already been finalized.

        Note that this function will clear any previous FIRST and FOLLOW set
        calculations. This function does NOT directly calculate the FIRST sets,
        but rather will implicitly fill them while creating the explicit
        FOLLOW sets. The definition for ``follow()`` allows for dynamic
        determination of FIRST sets, which makes this possible.

        Also note that this function will clear any existing parse table, so
        it is usually a good idea to call ``construct_ptable()`` after calling
        this function.
    
        In general, you don't need to call this function. It will be called
        during finalization.
        """
        if not self.finalized:
            self.finalize()

        # Initialize the parsing table
        self.ptable = {symbol: {terminal: [] for terminal in self.terminals}
                       for symbol in self.productions}
        # Initialize the (empty) FIRST and FOLLOW caches
        self.FIRST = {}
        self.FOLLOW = {symbol: set() for symbol in self.productions}
        self.FOLLOW[self.start[0]] |= {EOF}
        added_something_flag = True
        while added_something_flag:
            added_something_flag = False
            for symbol, rules in self.productions.items():
                for rule,action in rules:
                    for index in range(len(rule)):
                        rule_symbol = rule[index]
                        if rule_symbol.terminal():
                            continue
                        follow_set = self.FOLLOW[rule_symbol]
                        if index < len(rule)-1:
                            # "if there is more in this string"
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

    def error_check(self):
        """Raise GrammarError if the grammar is not LL(1).

        This function finalizes the parser if it has not already been finalized.

        If possible, this function will repair grammars which are not yet
        LL(1) but can be made so (ie, grammars that are left-recursive) by
        left-factoring. (This is not yet implemented.)

        In general, you don't need to call this function. It will be called
        during finalization.
        """
        if not self.finalized:
            self.finalize()

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

    def construct_ptable(self):
        """Construct the parse table for this parser.

        This function finalizes the parser if it has not already been finalized.

        In general, you don't need to call this function. It will be called
        during finalization.
        """
        if not self.finalized:
            self.finalize()

        for symbol, rules in self.productions.items():
            for rule,action in rules:
                for term in self.first(rule):
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
        """Use the recursive descent method to parse the input.

        The result will be an instance of ``pcc.parser.SyntaxTree``, which
        may be called with no arguments to retrieve the semantic action result
        of the parse.
        """
        if not self.finalized:
            self.finalize()
        lexer = _LexemeIterator(self.lexer,input)
        start_symbol, start_rule, start_action = self.start
        return SyntaxTree(_rd_parse_rule(
                            start_rule,start_action,lexer,self.ptable))

    def symbolize(self,rule):
        """LLParser.symbolize(string) -> pcc.symbols.SymbolString

        Creates a SymbolString out of a string based shorthand notation.
        
        This function identifies tokens, nonterminal symbols, and string
        literals in the rule and successfully creates the appropriate
        SymbolString object to represent it. This includes identifying
        previously defined tokens from this parser's lexer, AND includes
        creating new tokens out of string literals.

        In short summary, `rule` must be a string containing a whitespace
        seperated set of token or nonterminal symbol names. The tokens must
        be predefined by the lexer, but the nonterminals may be brand new.

        Seperate elements (tokens, nonterminals, and literals) of a rule must
        be seperated by whitespace, but any amount or kind of whitespace may
        be used. The rule may be empty, and may contain only whitespace - both
        cases produce an "epsilon" production (that is, a production which
        matches the empty string).

        A string literal is anything between two apostrophes (') in the rule
        string. This rule is greedy up to white space - that is, apostrophes
        themselves may occur between two apostrophes (denoting a string literal
        that matches an apostrophe at some point), but string literals **cannot
        contain any whitespace**. If you need to match whitespace, you are
        better off pre-defining a token that matches that whitespace. In
        general, you should treat string literals as a convenience, and not as
        the only way you define tokens.

        If the same string literal is defined twice in any set of rules (ie, in
        one or more calls to ``symbolize``), the exact same
        ``pcc.symbols.Token`` object will be generated.

        It is **extremely** important to note that this function has side
        effects in the parser - it will begin to fill out the production table
        with implicit symbols and will also add tokens to the lexer.
        """
        # I'm not 100% happy with this function due to the fact that it has
        # side effects and yet exists mostly as a helper function. It
        # shouldn't really ever be called by an end user, and yet it is
        # documented and 'protected' like it is meant to be useful to an end
        # user. For now, I'll leave it, because it is *big mojo* (turns BNF
        # rules in to symbolic productions - basically a mini-parser) and I
        # wouldn't want to roll it back in to the addproduction() code.
        if self.finalized:
            raise ValueError("Can't symbolize a rule after finalizing the "
                             "parser.")
        rule = rule.split()
        if not rule:
            return SymbolString((EPSILON,))

        result = []
        for label in rule:
            if label[0] == "'" and label[-1] == "'":
                # String Literal
                match_rule = re.escape(label[1:-1])
                if match_rule in self.literals:
                    result.append(self.literals[match_rule])
                else:
                    new_name = unique_string(self.lexer.tokens,
                                lower=False,number=False,prefix="LITERAL_")
                    new_literal = Token(new_name,match_rule)
                    self.lexer.addtoken(token=new_literal)
                    self.literals[match_rule] = new_literal
                    result.append(new_literal)
            elif re.match(SYMBOL_MATCH_RULE,label):
                # Symbol
                symbol = Symbol(label)
                if not symbol in self.productions:
                    # Implicit symbol
                    self.productions[symbol] = []
                result.append(symbol)
            elif re.match(TOKEN_MATCH_RULE,label):
                # Token
                if label not in self.lexer.tokens:
                    raise ValueError('Undefined token in rule "{}": "{}"'
                                     .format(rule,label))
                result.append(self.lexer.tokens[label])
    
            else:
                raise ValueError('Unknown expression in rule "{}": "{}"'.format(
                                 rule, label))
        return SymbolString(result)
        
def _rd_parse_rule(rule,action,lexer,parse_table):
    """Recursive function to parse the input"""
    children = []
    for symbol in rule:
        if symbol.terminal():

            if symbol == EPSILON:
                # epsilon-production - treat like input, but consume nothing
                children.append(SyntaxNode(None))
                continue
            
            next = lexer.poll()
    
            # if the wrong token is lexed:
            if next.token != symbol:
                raise ParsingError('Expected {} but found {} on line {} at '
                    'position {}'.format( symbol.name, next.match,
                    next.line, next.position))
            
            children.append(SyntaxNode(next.match))
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
            children.append(_rd_parse_rule(new_rule,new_action,lexer,
                            parse_table))
            continue
    # Parsing complete, now construct the AST node
    return SyntaxNode(action,children)

    
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
                        


