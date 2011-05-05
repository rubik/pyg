Pyg's features
==============

Pyg can:

    * Install packages from :file:`.tar.gz`, :file:`.tar.bz2`, :file:`.zip` archives, as well as from :file:`.egg` files and :file:`.pybundle` files.
    * Uninstall packages.
    * Define fixed sets of requirement.
    * Perform searches on PyPI.
    * Install from binaries (e.g. from :file:`.exe` or :file:`.msi`) on Windows.
    * Install packages in editable mode from VCS (Git, Mercurial, Bazaar, Svn).

Currently Pyg don't:

    * understand Setuptools extras (like ``package[extra]``)
    * integrate with virtualenv (planned for `Pyg v0.5`)


Pyg compared to easy_install
----------------------------

Pyg is meant to be a replacement for easy_install, and tries to improve it. In particular:

    * It can install packages from a name, URL, local directory or file.
    * It supports installation from requirements files.
    * It can install packages from Pip's bundels.
    * Easy yet very powerful uninstallation of packages.
    * It can perform searches on PyPI.
    * It offers the possibility to download a package without installing it.
    * Source code concise and cohesive and easily extensible.
    * Pyg can used either as a command-line tool or a Python library.
    * The output on the console should be useful.

But at the moment Pyg does not do everything that easy_install does:

    * It cannot install from binaries on Windows (i.e. from :file:`.exe` or :file:`.msi`).
    * It does not support Setuptools extras (like ``package[extra]``).


Pyg compared to Pip
-------------------

Pyg is very similar to Pip but tries to improve something. Specifically:

    * Pyg uses the same installation method as Pip but a different package discovery system that should be faster.
    * Pyg supports Python Eggs installation, while Pip doesn't.
    * A better uninstallation of packages (Pip cannot install packages installed with ``python setup.py install``).

But Pyg is not yet tested under virtualenv, unlike Pip.


Uninstall
---------

Pyg can uninstall most installed packages with::

    $ pyg uninstall packname

It tries to detect the directory where the packages have been installed and delete them.
Pyg can uninstall all packages, except those that have been installed in editable mode.

See also: :ref:`uninst`


Package upgrading
-----------------

This is a feature unique to Pyg: by running ``pyg update`` you can check all your installed packages and upgrade those for which there is a newer release.
Pyg collects all packages that can upgrade and then check for updates.

See also: :ref:`upd`

Pyg and virtualenv
------------------

.. versionadded:: 0.5

From Pyg 0.5 onwards, virtualenv is completely supported. You can easily manage packages from inside it.
A little example::

    $ virtualenv env -p /usr/bin/python2.6 --no-site-packages
    Running virtualenv with interpreter /usr/bin/python2.6
    New python executable in env/bin/python2.6
    Also creating executable in env/bin/python
    Installing setuptools............................done.
    $ cd env
    $ source bin/activate
    (env)$ pip install pyg
    (env)$ pyg install sphinx
    Looking for sphinx releases on PyPI
    Best match: Sphinx==1.0.7
    Downloading Sphinx
    Checking md5 sum
    Running setup.py egg_info for Sphinx
    Running setup.py install for Sphinx
    Installing dependencies...
    Installing Jinja2>=2.2 (from Sphinx==1.0.7)
            Looking for Jinja2 releases on PyPI
            Best match: Jinja2==2.5.5
            Downloading Jinja2
            Checking md5 sum
            Running setup.py egg_info for Jinja2
            Running setup.py install for Jinja2
            Installing dependencies...
    Installing Babel>=0.8 (from Jinja2==2.2)
            Looking for Babel releases on PyPI
            Best match: Babel==0.9.6
            Downloading Babel
            Checking md5 sum
            Running setup.py egg_info for Babel
            Running setup.py install for Babel
            Babel installed successfully
    Finished installing dependencies
    Jinja2 installed successfully
    Installing docutils>=0.5 (from Sphinx==1.0.7)
            Looking for docutils releases on PyPI
            Best match: docutils==0.7
            Downloading docutils
            Checking md5 sum
            Running setup.py egg_info for docutils
            Running setup.py install for docutils
            docutils installed successfully
    Installing Pygments>=0.8 (from Sphinx==1.0.7)
            Looking for Pygments releases on PyPI
            Best match: Pygments==1.4
            Downloading Pygments
            Checking md5 sum
            Running setup.py egg_info for Pygments
            Running setup.py install for Pygments
            Pygments installed successfully
    Finished installing dependencies
    Sphinx installed successfully
    (env)$ python
    Python 2.6.6 (r266:84292, Mar 25 2011, 19:24:58) 
    [GCC 4.5.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import sphinx
    >>> sphinx.__version__
    '1.0.7'
    >>>
    (env)$ pyg remove sphinx
    Uninstalling sphinx
            env/lib/python2.6/site-packages/Sphinx-1.0.7-py2.6.egg-info
            env/bin/sphinx-quickstart
            env/lib/python2.6/site-packages/sphinx
            env/bin/sphinx-build
            env/bin/sphinx-autogen
    Proceed? (y/[n]) y
    Deleting: env/lib/python2.6/site-packages/Sphinx-1.0.7-py2.6.egg-info
    Deleting: env/bin/sphinx-quickstart
    Deleting: env/lib/python2.6/site-packages/sphinx
    Deleting: env/bin/sphinx-build
    Deleting: env/bin/sphinx-autogen
    Removing egg path from easy_install.pth...
    sphinx uninstalled succesfully

Pyg Shell
---------

You can launch Pyg Shell with::

    $ pyg shell

and it will open a shell where you can use all Pyg's command. This is particularly useful on system where you need root privileges to installs packages (e.g. Unix): if you need to execute many commands you can fire up the shell and then use Pyg without worrying about root privileges.

See also: :ref:`shell`


Bundles
-------

Pyg supports Pip's bundles. The bundle format is specific to Pip (see `Pip documentation <http://www.pip-installer.org/en/latest/index.html#bundles>`_).
Once you have one you can install it like::

    $ pyg install yourbundle.pyb

The internet access is not necessary.

See also: :ref:`bundles`