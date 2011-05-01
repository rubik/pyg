Checking installed packages
===========================

If you want to check if a package is installed, you can use the ``check`` command::

    $ pyg check packname

Some examples::

    $ pyg check pyg
    True
    $ pyg check pyg==42
    False
    $ pyg check pyg==0.1.2
    True
    $ pyg check pyg==0.1.3
    False


Searching PyPI
==============

Pyg can perform searches on PyPI with the ``search`` command::

    $ pyg search pypol_
    pypol_  0.5 - Python polynomial library
    pypolkit  0.1 - Python bindings for polkit-grant

    $ pyg search distribute
    distribute  0.6.15 - Easily download, build, install, upgrade, and uninstall Python packages
    virtualenv-distribute  1.3.4.4 - Virtual Python Environment builder


Linking directories
===================

If you want to add a directory to :envvar:`PYTHONPATH` permanently the ``link`` command is what you need::

    $ pyg link dirname

When you link a directory Pyg add in a :file:`.pth` file the dir's path.


Unlinking
=========

.. program:: unlink

If you want to remove a directory from :envvar:`PYTHONPATH` you can use the ``unlink`` command.
Pyg can remove a directory from :envvar:`PYTHONPATH` only if that directory has been added previously.

.. option:: -a, --all

    Remove all links in the :file:`.pth` file.