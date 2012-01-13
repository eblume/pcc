Python Compiler Compiler (``pcc``)
=============================

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

About This Document
-------------------

The documentation for ``pcc`` is generated automatically. The first section of
the official documentation comes directly from the ``README.rst`` file at the
root level of the ``pcc`` project - and you may in fact be reading from that
file right now! Alternately, you could be reading from "pcc.pdf", which is the
full documentation for ``pcc``.

How to use "pcc.pdf"
~~~~~~~~~~~~~~~~~~~~

The first section of "pcc.pdf" comes directly from ``README.rst``, and you are
reading it now. The second section is the Cookbook - **new developers will
(hopefully) find the Cookbook as a helpful place to start.** The Cookbook
contains color-coded and well-explained code examples on how to use ``pcc``.

Finally, the third section (entitled "``pcc`` Package") is the automatically
generated API documentation that comes directly from the code itself. Notably,
any code examples in this section are actually executed as part of the testing
suite (see Testing, below). One thing to note about this documentation is that
you can generally skip any module with "_test" at the end of its name - this
denotes a module that contains only unit test cases, and thus isn't of much
use to anyone other than a ``pcc`` developer.

How to regenerate "pcc.pdf"
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you suspect your documentation is out of date, you can re-generate it by
going in to the ``docs/`` subdirectory of this project and executing::

    $ make pcc

Assuming you have all the required packages (LaTeX and Sphinx are both required,
for instance - although some python packages may hopefully install themselves)
the "pcc.pdf" file will be updated automatically.

Installation
------------

``pcc`` uses ``distribute``, a ``setuptools``-like distribution wrapper, to
automate installation.

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

No errors should be reported by this process. Also note that while setuptools
may report that there is a ``tests`` command, this has not been configured - use
``nosetests`` instead.

Release History
---------------

0.1 - 13 January 2012
    Working LL(1) parser with semantic actions.

Contributing
------------

See AUTHORS for a (hopefully) complete list of all contributors to this project.
Please add your name and - if you like - your email to the list if you
contributed anything you felt was meaningul to the project.

For tips and procedures on how to contribute - or to report a bug or leave
feedback - please visit the ``pcc`` project page on
`github <https://github.com/eblume/pcc>`_. Please feel free to be bold in
submitting patches, tickets, or push requests - I won't be offended and would
greatly appreciate the effort!


