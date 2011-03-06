.. pyg documentation master file, created by
   sphinx-quickstart on Sat Mar  5 09:31:18 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyg's documentation!
===============================

pyg is a Python Package Manager.

Pyg's features
--------------

pyg can:

    * install packages from :file:`.tar.gz`, :file:`.tar.bz2`, :file:`.zip` archives, as well as from :file:`.egg` files and :file:`.pybundles`
    * uninstall packages
    * define fixed sets of requirement
    * perform searches on PyPI

Currently pyg cannot:
    * install from binaries (e.g. from :file:`.exe` or :file:`.msi`)
    * install packages in editable mode from VCS (GitHub, Bitbucket, Bazaar, Svn)


Uninstall
---------

pyg can uninstall most installed packages with ``pyg uninstall packname``.

It tries to detect the directory where the packages have been installed and delete them.
pyg can uninstall almost all packages, except those that have been installed in editable mode. 


.. toctree::
   :maxdepth: 2

