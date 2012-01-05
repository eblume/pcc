Python Compiler Compiler (pcc)

Context Free Grammar parsers for Python 3

Copyright 2012 Erich Blume <blume.erich@gmail.com>

License & Copying Notice
------------------------

This file is part of pcc.

pcc is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pcc is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pcc, in a file called COPYING.  If not, see
<http://www.gnu.org/licenses/>.

Installation
------------

pcc uses ``distribute``, a ``setuptools``-like distribution wrapper, to automate
installation.

Requirements
~~~~~~~~~~~~
* `Python 3.0 or higher <http://python.org/download/>`_

Installation on Linux / OS X
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Execute the following command (or similar) to install the module for all users::

    $ sudo python3 setup.py install

You can also see a more complete list of build options by entering::

    $ python3 setup.py --help

or by reading the ``distribute`` documentation.

Installation on Windows
~~~~~~~~~~~~~~~~~~~~~~~

Coming soon! This should be fairly simple, as ``distribute`` should take care
of the tricky stuff. It probably works already, I just haven't tested it yet.

Testing
~~~~~~~

It is a good idea to run the unit test suite, and it is generally very simple
to do so. Unit testing is performed using ``nose``, and is automated by 
``distribute``, and augmented with testing coverage reports by ``coverage``.

To execute the full testing suite, enter the following command::

    $ python3 setup.py nosetests

No errors should be reported by this process.

Documentation
-------------

Please see "pcc.pdf" at the root project directory for the complete
documentation. The ``docs`` directory can be ignored unless you wish to edit or
regenerate the documentation from the source.

To regenerate the documentation (generally only performed by me before a
release), go to the ``docs`` directory and execute the following command::

    $ make pcc

This will automatically (using `Sphynx <http://sphinx.pocoo.org/>`_) scan the
source code, build the API documentation in to ReStructuredText, transcribe the
docs to LaTeX, and compile the LaTeX source in to "pcc.pdf" at the project's
root directory.

Release History
---------------

No release has been made yet. How cool are you?

Contribution
------------

See AUTHORS for a (hopefully) complete list of all contributors to this project.
Please add your name and - if you like - your email to the list if you
contributed anything you felt was meaningul to the project.

For tips and procedures on how to contribute - or to report a bug or leave
feedback - please visit the pcc project page on
`github <https://github.com/eblume/pcc>`_. Please feel free to be bold in
submitting patches, tickets, or push requests - I won't be offended and would
greatly appreciate the effort!


