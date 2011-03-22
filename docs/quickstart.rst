Quickstart
==========

Installing Pyg
--------------

To install Pyg it only takes one simple command::

    $ pip install pyg

or if you must::

    $ easy_install pyg

And then you should no longer need them.

.. _get:

Getting the Source
------------------

You can also install Pyg from the source. The lastest release is avaiable on GitHub:

    * `tarball <https://github.com/rubik/pyg/tarball/master>`_
    * `zipball <https://github.com/rubik/pyg/zipball/master>`_

Once you have unpacked the archive you can install it easily::

    $ python setup.py install


Building the documentation
--------------------------

In order to build Pyg's documentation locally you have to install `Sphinx <http://sphinx.pocoo.org>`_::

    $ pyg install sphinx

Download the source (see :ref:`get`) and go to :file:`docs/` and run :command:`make`::

    $ cd docs/
    $ make html

Now Pyg's documentation is in :file:`_build/html`.


Now that Pyg is installed you may want to read:

:ref:`cmdline`