Quickstart
==========

Installing Pyg
--------------

The :file:`get-pyg.py` file
+++++++++++++++++++++++++++++

The preferred way to install Pyg (and the easiest one) is to download the :file:`get-pyg.py` file from `Github <https://raw.github.com/rubik/pyg/master/get-pyg.py>`_ and to launch it::

    $ curl -O https://raw.github.com/rubik/pyg/master/get-pyg.py
    $ python get-pyg.py

This will install the latest stable release, but if you want to install the development version, just do::

    $ python get-pyg.py --dev


Using ``Pip`` or ``easy_install``
+++++++++++++++++++++++++++++++++

If you have ``easy_install`` or ``Pip`` installed, to install Pyg it only takes one simple command::

    $ pip install pyg

or if you must::

    $ easy_install pyg

And then you should no longer need them!

.. _get:

Getting the source
------------------

You can also install Pyg from source. The lastest release is avaiable on GitHub:

    * `tarball <https://github.com/rubik/pyg/tarball/master>`_
    * `zipball <https://github.com/rubik/pyg/zipball/master>`_

Once you have unpacked the archive you can install it easily::

    $ python setup.py install


Building the documentation
--------------------------

In order to build Pyg's documentation locally you have to install `Sphinx <http://sphinx.pocoo.org>`_::

    $ pyg install sphinx

Download the source (see :ref:`get`), go to :file:`docs/` and run :command:`make`::

    $ cd docs/
    $ make html

Now Pyg's documentation is in :file:`_build/html`.