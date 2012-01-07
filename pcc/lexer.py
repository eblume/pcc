"""lexer.py - Tokenize lexemes from strings, similar to F/Lex, but Pythonic."""
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
import pcc.symbols as symbols

_token_ident = re.compile(r'[a-zA-Z][_a-zA-Z0-0]*')

class Lexer:
    r"""Create a new Lexer object.

    If `ignore_whitespace` is left True, a token called WHITESPACE will
    be created with the rule ``r"\s+"`` with the `silent` option on - the
    effect of which is that bare whitespace will be effectively stripped
    from the input. Note that this overrides `ignore_newlines`.

    If `ignore_newlines` is left True but `ignore_whitespace` is False, then
    a new token called NEWLINE will be added with the rule ``r"[\n]+"`` and
    the `silent` option on.

    For either of these whitespace-skipping rules, keep in mind that you
    can still have tokens with whitespace due to the greedy nature of
    pattern matching.

    If `report_literals` is left True, a token that matches one (and only one)
    non-whitespace character will be added. This accomplishes two things: it
    helps (particularly alongside ignore_whitespace) to avoid ``lex()`` ever
    raising an error because no rule matches the input stream, and it also
    allows your parser to interpret literal strings in a grammar. This token
    will be called LITERAL, and `silent` will be (of course) off.

    >>> p = Lexer()
    >>> p.addtoken(name='NAME',rule=r'[_a-zA-Z][_a-zA-Z0-9]+')
    >>> p.addtoken(name='REAL_NUMBER',
    ...            rule=r'(-)?([1-9][0-9]*(\.[0-9]+)?|0\.[0-9]+)')
    >>> p.addtoken(name='TWO_WORDS',rule=r'[a-zA-Z]+ [a-zA-Z]+')
    >>> p.addtoken(name='MULTI_LINE',rule=r'foo\nbar')
    >>> input = '''42 is a number
    ... 3.14159 foo
    ... bar sameline
    ... _Long_Identifier_ banana
    ... ocelot!!
    ... '''
    >>> for lexeme in p.lex(input):
    ...     print("{} > {} | {},{}".format(lexeme.token.name, lexeme.match,
    ...                                    lexeme.line, lexeme.position))
    REAL_NUMBER > 42 | 1,1
    TWO_WORDS > is a | 1,4
    NAME > number | 1,9
    REAL_NUMBER > 3.14159 | 2,1
    MULTI_LINE > foo
    bar | 2,9
    NAME > sameline | 3,5
    NAME > _Long_Identifier_ | 4,1
    NAME > banana | 4,19
    NAME > ocelot | 5,1
    LITERAL > ! | 5,7
    LITERAL > ! | 5,8

    """
    def __init__(self, ignore_whitespace=True, ignore_newlines=True,
                 report_literals=True):
        self.tokens = {}

        if report_literals:
            self.addtoken(name='LITERAL',rule=r'\S')

        if ignore_whitespace:
            self.addtoken(name='WHITESPACE',rule=r'\s+', silent=True)
        elif ignore_newlines:
            self.addtoken(name='NEWLINE',rule=r'[\n]+', silent=True)

    def addtoken(self,token=None, name=None, rule=None, silent=False):
        """Add the specified ``pcc.symbols.Token`` object to the lexer.
        
        Either `token` or both `name` and `rule` need to be specified.

        `token`, if used, must be a ``pcc.symbols.Token`` object which will
        be used in the manner described in that classes documentation. The
        `silent` flag from this function will be ignored, and instead the same
        field from the ``Token`` object will be honored.

        If `token` is not specified, then `name` and `rule` must be this
        new token's name and lexing regular expression respectively. As per
        ``pcc.symbols.Token``'s documentation, the `silent` flag denotes that
        this token will not be yielded by this ``Lexer``'s ``lex`` generator,
        although the token may still consume input. This is useful for 
        ignoring whitespace and comments, if that is desired.

        The name of the token must be unique to this ``Lexer``.
        """
        if token is None and (name is None or rule is None):
            raise ValueError('For addtoken(), must specify token or name and '
                             'rule')

        if token is None:
            token = symbols.Token(name,rule,silent)

        if token.name in self.tokens:
            raise ValueError('Token {} already exists.'.format(token))

        self.tokens[token.name] = token
        

        

    def lex(self,input):
        """Generator that produces ``Lexeme`` objects from the input string."""
        if len(self.tokens) < 1:
            raise ValueError('The lexer must have at least 1 rule to work.')

        line = 1
        line_pos = 1
        position = 0
        end = len(input)

        while position < end:
                      # This is a tuple (name,match_object,silent_flag)
            matches = [(token, token.match(input,position))
                       for token in self.tokens ]
            # Prune out all non-matches and 0-length matches
            matches = [(token,match) for token,match in matches
                       if match and len(match) > 0 ]
            if len(matches) == 0:
                raise ValueError('No token was found at line {} position '
                                 '{}.'.format(line,line_pos))
            # Sort the matches by match length, descending.
            matches.sort(reverse= True, key=lambda x: len(x[1]))

            # Pull out the top match
            #     TODO: are we sure we want to do this, or rather Error?
            top_token, top_match = matches[0]

            if not top_token.silent:
                yield Lexeme(top_token,top_match,line,line_pos)

            # Advance line and line_pos as needed.
            line_count = top_match.count("\n")
            line += line_count
            if line_count > 0:
                line_pos = len(top_match.split("\n")[-1]) +1
            else:
                line_pos += len(top_match)

            position += len(top_match)
            
            
    
class Lexeme:
    """Input (string) that has been matched to some ``Token``.

    Every ``Lexeme`` object has the fields ``name``, ``match``, ``line``, and
    ``position``.
    """
    def __init__(self, token, match, line, position):
        self.token = token
        self.match = match
        self.line = line
        self.position = position
