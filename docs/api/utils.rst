.. highlight:: python

:mod:`pyg.utils` --- Utility functions
======================================

.. module:: pyg.utils
    :synopsis: Utility functions

.. moduleauthor:: Michele Lacchia <michelelacchia@gmail.com>
.. sectionauthor:: Michele Lacchia <michelelacchia@gmail.com>


This module defines some constants:

.. data:: USER_SITE

    Path to the user site directory for the current Python version or None.

.. data:: INSTALL_DIR

    Path to eggs installation directory. On Python 2.7 it is equivalent to::

        import site
        site.getsitepackages()[0]

    On Python 2.6 it is quite more complicated, and if the process fails, this constant will be set to::

        from distutils.sysconfig import get_python_lib
        INSTALL_DIR = get_python_lib()

.. data:: EASY_INSTALL

    Path to :file:`easy_install.pth` file. If it does not exist, will be created.

.. data:: PYG_LINKS

    A Pyg's :file:`.pth` file under :data:`USER_SITE`.

.. data:: BIN

    Path to the directory which contains scripts.