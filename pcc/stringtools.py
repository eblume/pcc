"""stringtools.py - miscellaneous string utility functions
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

import itertools

def unique_string(existing,length=6,lower=True,upper=True,number=True,
                  prefix=None, suffix=None):
    """Generate a new string that is not a member of `existing`.

    `existing` should be a set, but any object that supports the *in* syntax for
    querying membership will work.

    `length` will be the length of the generated string.

    If `lower` is left as True, the string will be generated using lowercase
    letters. If `upper` is True, uppercase letters will be used. If `number` is
    True, numbers will be used. These options may be combined. At least one
    must be turned on.

    If `prefix` or `suffix` are set to some string, then that string will be
    prepended or appended to every generated string before testing for
    uniqueness. The result will be a prefixed and/or suffixed string with some
    random kernel, in which the kernel alone is the length specified by
    `length`. In other words, `length` does not apply to the prefix or the
    suffix.

    >>> pre = {'one','two','another_string',"Any length works","sixsix"}
    >>> unique_string(pre) in pre
    False
    >>> unique_string(pre,upper=False) in pre
    False
    >>> unique_string(pre,lower=False,upper=False,number=False) in pre
    Traceback (most recent call last):
        ...
    ValueError: You must specify at least one of the generating sets
    >>> pre = {"0","1","2","3","4","5","6","7","8","9"}
    >>> unique_string(pre,lower=False,upper=False,length=1) in pre
    Traceback (most recent call last):
        ...
    ValueError: The specified existing set is already full for this length
    >>> unique_string(pre,lower=False,upper=False,length=1,prefix="_",
    ... suffix="_") in pre
    False
    """
    gen_set = ""
    if lower:
        gen_set += "abcdefghijklmnopqrstuvwxyz"
    if upper:
        gen_set += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if number:
        gen_set += "0123456789"

    if not gen_set:
        raise ValueError("You must specify at least one of the generating sets")

    for gen in itertools.product(gen_set,repeat=length):
        gen = "".join(gen)
        if prefix:
            gen = prefix + gen
        if suffix:
            gen = gen + suffix
        if gen not in existing:
            return gen
    
    raise ValueError("The specified existing set is already full for this "
                     "length")
    




