Pyg's features
==============

Pyg can:

    * install packages from :file:`.tar.gz`, :file:`.tar.bz2`, :file:`.zip` archives, as well as from :file:`.egg` files and :file:`.pybundles`
    * uninstall packages
    * define fixed sets of requirement
    * perform searches on PyPI

Currently Pyg cannot:
    * install from binaries (e.g. from :file:`.exe` or :file:`.msi`)
    * install packages in editable mode from VCS (GitHub, Bitbucket, Bazaar, Svn)


Uninstall
---------

Pyg can uninstall most installed packages with ``Pyg uninstall packname``.

It tries to detect the directory where the packages have been installed and delete them.
Pyg can uninstall all packages, except those that have been installed in editable mode.

.. seealso::
    :ref:`uninst`