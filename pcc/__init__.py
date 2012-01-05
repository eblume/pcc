# __init__.py - package metafile for pcc
# Copyright 2012 Erich Blume <blume.erich@gmail.com>
# ===========================
#
# This file is part of pcc.
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

"""pcc - Create parsers for context free grammars (CFGs).

See ``pcc.lexer`` for a lexical analyzer/tokenizer class.

See ``pcc.parser`` for several implementations of CFG parser generators that
utilize the ``Lexer`` class from ``pcc.lexer``.

"""

# VERSION_INFO
# A tuple of strings (version, release).
# Version is the major version number of the software.
# 
# Release is in the form A.B where A is the Version and B is the minor version.
# Release may have any of the following suffixes:
#   -dev : Software is currently in a development (alpha) phase.
#   -rc# : Software is prepared for release, and is the #'th release candidate.
#   -beta: Software is currently in a 'special' (beta) release.
# No suffix means that the software is currently in an official release state.

VERSION_INFO=("0","0.1-dev")

