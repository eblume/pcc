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

_token_ident = re.compile(r'[a-zA-Z][_a-zA-Z0-0]*')

class Lexer:
    def __init__(self, ignore_whitespace=True, ignore_newlines=True,
                 report_literals=True):
        r"""Create a new Lexer object.

        If `ignore_whitespace` is left True, a token called WHITESPACE will
        be created with the rule r"\s+" with the `silent` option on - the
        effect of which is that bare whitespace will be effectively stripped
        from the input. Note that this overrides `ignore_newlines`.

        If `ignore_newlines` is left True but `ignore_whitespace` is False, then
        a new token called NEWLINE will be added with the rule r"[\n]+" and the
        `silent` option on.

        For either of these whitespace-skipping rules, keep in mind that you
        can still have tokens with whitespace due to the greedy nature of
        pattern matching.

        If `report_literals` is True, then in the case that no token matches the
        current input sequence, rather than raising an error, a token with the
        name 'LITERAL' will be created with the next character of input (and
        only one character).

        >>> p = Lexer()
        >>> p.addtoken('NAME',r'[_a-zA-Z][_a-zA-Z0-9]+')
        >>> p.addtoken('NUMBER',r'[0-9]+')
        >>> p.addtoken('REAL_NUMBER',r'(-)?([1-9][0-9]*(\.[0-9]+)?|0\.[0-9]+)')
        >>> p.addtoken('TWO_WORDS',r'[a-zA-Z]+ [a-zA-Z]+')
        >>> input = '''42 is a number
        ... 3.14159
        ... _Long_Identifier_ banana
        ... ocelot!!
        ... '''
        >>> for token in p.lex(input):
        ...     print("{} > {} | {},{}".format(token.name, token.match,
        ...                                    token.line, token.position))
        NUMBER > 42 | 1,0
        TWO_WORDS > is a | 1,3
        NAME > number | 1,8
        REAL_NUMBER > 3.14159 | 2,0
        NAME > _Long_Identifier_ | 3,0
        NAME > banana | 3,18
        NAME > ocelot | 4,0
        LITERAL > ! | 4,6
        LITERAL > ! | 4,7

        """
        self.tokens = {}
        if ignore_whitespace:
            self.addtoken('WHITESPACE',r'\s+', silent=True)
        elif ignore_newlines:
            self.addtoken('NEWLINE',r'[\n]+', silent=True)

        self.literals = report_literals

    def addtoken(self,name,rule, silent=False):
        """Add a token-generating rule.

        `name` is a unique (to this Lexer) identifier which must match the
        regular expression "[a-zA-Z][_a-zA-Z0-9]*" - it may also not be named
        'LITERAL', as this is reserved. Classically (and to help avoid
        conflicts with parser symbols), all tokens should be named in all
        capitals with underscores between words.

        `rule` is a regular expression in a string (preferably a 'raw' string,
        but that's up to the user) that will be passed to re.match to find a
        token. Avoid using complex regular expressions to avoid breaking the
        system - try to just use literals, literal groups, and quantifiers, and
        definitely do not use position metacharacters like "^" and "$" or back-
        -references.
        
        `silent`, if set to True, will supress the generation of this token as
        a result from the ``lex`` method. In this case, the token will still be
        lexed (and input consumed), but the ``lex`` method won't generate the
        token as output.
        """

        if name == "LITERAL" or not _token_ident.match(name):
            raise ValueError('Token name {} is invalid.'.format(name))

        if name in self.tokens:
            raise ValueError('Token name {} already exists.'.format(name))

        self.tokens[name] = (re.compile(rule),silent)

        

    def lex(self,input):
        """Generator that produces Token objects from the input string."""
        # IMPORTANT NOTE: There is currently a bug in which if two tokens
        # both tie for the best match, one will be chosen essentially at
        # random (by the sorting algorithm). In theory, this should produce
        # an error instead. However, checking this is costly - and the
        # semi-random non-crashing behavior of the bug is probably preferable.

        if len(self.tokens) < 1:
            raise ValueError('The lexer must have at least 1 rule to work.')

        line = 1
        line_pos = 0
        position = 0
        end = len(input)

        # TODO - this algorithm is very brute force, and essentially works
        # by running the regexp from every token for every step of the input.
        # There MUST be a much better way, probably by doing some sort of
        # regexp combining or - if I really want to recreate Lex/Yacc - a
        # finite-state automaton. For now we will use this brute force method,
        # for although it is not ideal, it seems fast enough for the intended
        # use case.

        while position < end:
                      # This is a tuple (name,match_object,silent_flag)
            matches = [ (name, matcher[0].match(input,position),matcher[1])
                       for name, matcher in self.tokens.items()]
            # Prune out all non-matches and 0-length matches
            matches = [ x for x in matches if x[1] and len(x[1].group(0)) > 0]
            if len(matches) == 0:
                if self.literals:
                    # Inject a fake 'LITERAL' token
                    match_name = 'LITERAL'
                    silent = False
                    match_text = input[position]
                else:
                    raise ValueError('No token was found at line {} position '
                                     '{}.'.format(line,line_pos))
            else:
                # Sort the matches by match length, descending.
                matches.sort(
                             reverse= True,
                             key= lambda x: len(x[1].group(0))
                            )
    
                match_name, match_object, silent = matches[0]
                match_text = match_object.group(0)

            if not silent:
                yield Token(match_name,match_text,line,line_pos)

            # Advance line and line_pos as needed.
            line_count = match_text.count("\n")
            line += line_count
            if line_count > 0:
                line_pos = len(match_text.split("\n")[-1])
            else:
                line_pos += len(match_text)

            position += len(match_text)
            
            
    
class Token:
    """A container for a token name, a bit of input that matched that token's
    lexing rule, and the position in the input stream at which it occured.

    Every Token object has the fields ``name``, ``match``, ``line``, and
    ``position``.
    """
    
    def __init__(self, name, match, line, position):
        self.name = name
        self.match = match
        self.line = line
        self.position = position
