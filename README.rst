WARNING - Important notice
==========================

This project is now **DEAD**.
It was born with the intent to provide a better (IMHO) alternative to Pip.
Since now Pip has got a lot of great improvements, this is not needed anymore.

So the advice here is to use Pip instead. Pyg has not been maintained for over
2 years now. It may well be broken in many places. The code is old and would
need a refactoring, but there is not need anymore.


Pyg
===

Pyg is a Python Package Manager that is meant to be an alternative to easy_install.

Installation
-----------

To install Pyg it takes only one simple command::

    $ pip install pyg

or if you must::

    $ easy_install pyg

And then you should no more need them!

Installing from source
----------------------

Also, you can download the source and after unpacking the archive::

    $ python setup.py install


**Note:** You may need root privileges to install.

Documentation
------------

If you need further information you can check the documentation at: http://pyg-installer.co.nr

Building the documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can build the documentation locally. In order to build the html documentation you need to install `Sphinx`_. Simply run::

    $ pyg install sphinx

Again, you may need root privileges.
Now you can build the docs. If you haven't already downloaded the source download it and open your terminal::

    $ cd docs
    $ make html

The docs are now in ``_build/html/``


.. _Sphinx: http://sphinx.pocoo.org
