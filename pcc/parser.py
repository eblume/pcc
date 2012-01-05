""" parser.py - CFG parsing with python functions as semantic actions

Create Parser objects, which take tokenized input (via lexer.py) and use
different parsing methods to synthesize BNF rules in to productions with
semantic python actions. All semantic actions are python functions that take a
list as an argument (representing the values of sub-expressions) and return a
value as the result for that expression.

Use the helper method ``parser()`` to create a Parser object if you don't
care about what algorithm it will use. Otherwise, you cannot instantiate a
Parser object directly, but must instead use on of its subclasses, each of
which uses a slightly different algorithm. (It is the author's plan to use this
setup as a way to read through the 'Purple Dragon Book' - Aho, Lam, Sethi, and
Ullman.
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

class GrammarError(Exception):
    """Exception raised by a parser.Parser object *before* parsing begins."""
    pass

class SyntaxError(Exception):
    "Exception raised by a parser.Parser object when a syntax error occurs."
    pass

def parser():
    """Create a parser.Parser object using the default algorithm."""
        

class Parser(metaclass=ABCMeta):
    """CFG parser of arbitrary BNF-like rules.

    Actual implementations should subclass this abstract base class, and may
    have slightly different levels of 'computational power'. That is to say,
    an LL language is slightly less expressive than an SLR, which is less
    expressive than an LALR, which is less expressive than an LR language.
    All are essentially 'context free grammars'. If a parser encounters an
    error before parsing has begun (ie. an error with a rule) then
    ``parser.GrammarError`` should be raised. If a parser encounters a syntax
    error during parsing, then ``parser.SyntaxError`` should be raised. Other
    errors should be reported in the most reasonably expressive manner possible.

    Use ``addrule`` to add rules with semantic actions. Use ``parse`` to
    execute parsing. Parsing is immediate and returns no value, unlike other
    LALR parsers which might work stepwise - this is because this class takes
    advantage of python generator functions.

    The following example emulates this simple grammar (in bison/YACC form:)

    expr : expr '+' term   { $$ = $1 + $3; }
         | expr '-' term   { $$ = $1 - $3; }
         | term            { $$ = $1; }
         ;
    
    term : '(' expr ')'    { $$ = $2; }
         | num             { $$ = $1; }
         ;

    num : '0'              {$$ = 0; }
        | '1'              {$$ = 1; }
        [.... etc, for each number 0-0 ....]
        ;

    >> l = Lexer()
    >> l.addtoken('NUMBER',r'[0-9]+')
    >> p = parser(l)
    >>
    >> p.addrule('prog', "expr", lambda v: print(v[0]))
    >> 
    >> p.addrule('expr', "expr '+' term", lambda v: v[0] + v[2])
    >> p.addrule('expr', "expr '-' term", lambda v: v[0] - v[2])
    >> p.addrule('expr', "term", lambda v: v[0])
    >>
    >> p.addrule('term', " '(' expr ')' ", lambda v: v[1])
    >> p.addrule('term', " NUMBER ", lambda v: v[0])
    >>
    >> p.parse("5-(9+2)")
    -6

    """

    @abstractmethod
    def addrule(self,symbol,rule,action):
        """Add a production (rule) to the grammar of the parser. Instructs the
        parser that `symbol` can be derived using `rule`, producing a result
        via `action`.

        `symbol` is a string that must match the regular expression
            r'[a-zA-Z]+'
        Note that it is not allowed for a symbol to have the same name as
        a token that might be produced by the lexer. Therefor, if you try
        to add a rule with a `symbol` that is already the name of a token,
        ValueError will be raised immediatly, and the rule will not be added.

        `rule` is a string that has whitespace seperated terminal and
        nonterminal symbols (see below). It may also be a list of such strings
        (with all whitespace stripped). In other words, if the rule is
            "foo '*' bar"
        you could equivalently use rule.split() - both work just as well.

        `action` is a function (often a lambda expression, but there is no
        such requirement) that takes a list as input and may return some value.
        The list will be filled with returned values of the derivation actions
        of the symbols in the rule, in order, starting from 0. (See the example
        in the Parser class documentation for a more clear explanation.)
        Alternately, action may be any other value, in which case that value
        will be used for upper derivation actions direcly.

        You may define rules that derive the same symbol any number of times,
        but keep in mind that what you are doing is defining multiple
        derivations. All symbols used in a rule must have a derivation before
        parsing, although you can use a symbol in a new rule before it has
        a derivation (so long as you eventually give it a derivation).

        Terminal and Nonterminal Symbols
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Recall that the `rule` parameter is a whitespace-seperated strings of
        'symbols' (or a list of symbols). A symbol is defined as either:

        1. All of the named tokens in the lexer, which have names conforming to
          the regex found in lexer._token_ident (at this writing,
          r'[a-zA-Z][_a-zA-Z0-9]*').
        2. String literals, which are identified in the rule as any single
          character between two single quotes (including, possibly, a single
          quote itself - which would be three single quotes one after another.)
        3. Any nonterminal symbol (see below), although keep in mind that all
          nonterminal symbols must have at least one derivation before parsing
          can commense.

        1 and 2 describe "terminal symbols", in that they have no derivations
        and exist directly in the input stream. 3, the nontermimal symbols,
        are exactly the set of strings called "symbol" that get passed to this
        function (`addrule`).

        Note that string literals are only supported when using
        ``lexer.Lexer``'s `report_literals` option (which is on by default).
        It is also perfectly acceptable to use "LITERAL" as a named token, but
        recall that this will match *any* string literal, not just the specific
        one you could have given if you had used the single-quote shortcut.

        It is currently very combursome to try and match multi-character string
        literals, so it is generally suggested to wrap such keywords in a
        token specificically for that keyword instead.

        """
        raise NotImplementedError("Attempt to call an abstract method.")

    @abstractmethod
    def parse(self,input):
        """Parse the given `input` (a string) using the given rules and lexer.

        Note that some parser generators produce parsers that will return
        an Abstract Syntax Tree (AST) as a result, allowing the caller to
        walk the tree and produce the desired final product. However, this
        parser does not do that.

        Instead, this function will return nothing, but will produce the
        desired final product by means of the `action` functions given in
        ``Parser.addrule``. 
        """
        pass

