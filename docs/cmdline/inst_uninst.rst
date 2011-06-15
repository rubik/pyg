Installing and removing packages
================================

Installing
----------

.. program:: install

To install a package, simply run::

    $ pyg install package

*package* can be a number of things:

    * the name of the package you want to install (e.g. ``pyg`` or ``sphinx``)
    * a package URL (e.g. ``http://www.example.org/path/to/mypackage-0.1.tar.gz``)
    * a local file (like ``path/to/mypackage-0.42-py2.7.egg``)
    * a local directory containing a :file:`setup.py` file
    * a repository URL (like ``git+git@github.com/rubik/pyg``)
    * a gist URL (i.e. ``gist+928471``)

Pyg supports these file-types:

    * :file:`.tar.gz`
    * :file:`.tgz`
    * :file:`.tar.bz2`
    * :file:`.zip`
    * :file:`.egg`
    * :file:`.exe`
    * :file:`.msi`
    * :file:`.pybundle`
    * :file:`.pyb` (an abbreviation of Pip's bundle files)

.. option:: -e <URL>, --editable <URL>

    Install a package in editable mode (``python setup.py develop``) from an online repository. Supported VCS are:

        * Git (prefix ``git+``)
        * Mercurial (prefix ``hg+``)
        * Bazaar (prefix ``bzr+``)
        * Subversion (prefix ``svn+``)

    The URL syntax is as follows::

        <prefix><repo_url>#egg=<package_name>

    All fields are required. The last part (``#egg=<package_name>``) specifies the package name.

    .. versionadded:: 0.3

.. option:: --no-script

    Do not install packages' scripts.

    .. versionadded:: 0.3

.. option:: --no-data

    Do not install packages' data files.

    .. versionadded:: 0.3

.. option:: -r <path>, --req-file <path>

    Install packages from the specified requirement file::

        $ pyg install -r requirements.txt

    See also: :ref:`reqs`

.. option:: -U, --upgrade

    If the package is already installed, install it again.
    For example, if you have installed ``pypol_ v0.4``::

        $ pyg install pypol_==0.4
        Best match: pypol_==0.4
        Downloading pypol_
        Checking md5 sum
        Running setup.py egg_info for pypol_
        Running setup.py install for pypol_
        pypol_ installed successfully

    Later you may want to re-install the package. Instead of running :command:`remove`` and then :command:`install`, you can use the :option:`-U` option::

        $ pyg install -U pypol_
        Best match: pypol_==0.5
        Downloading pypol_
        Checking md5 sum
        Installing pypol_ egg file
        pypol_ installed successfully

    This command **does not** upgrade dependencies.

    .. versionadded:: 0.2

.. option:: -A, --upgrade-all

    Like, :option:`install --upgrade`, but upgrade dependencies too.

    .. versionadded:: 0.5

.. option:: -n, --no-deps

    Do not install package's dependencies.

.. option:: -i <url>, --index-url <url>

    Specify the base URL of Python Package Index (default to ``http://pypi.python.org/pypi``).

.. option:: -d <path>, --install-dir <path>

    The base installation directory for all packages.

.. option:: -u, --user

    Install the package in the user site-packages.


.. _uninst:

Uninstalling
------------

.. versionchanged:: 0.5

    Replaced :command:`uninstall` and :command:`rm` with :command:`remove`.

Removing a package is dead simple::

    $ pyg remove packname

Pyg tries to detect the package's folder and delete it::

    $ pyg remove sphinx
    Uninstalling sphinx
            /usr/bin/sphinx-build
            /usr/local/lib/python2.7/dist-packages/Sphinx-1.0.7-py2.7.egg
            /usr/bin/sphinx-quickstart
            /usr/bin/sphinx-autogen
    Proceed? (y/[n]) 


If *packname* is a module and not a package, Pyg will automatically detect it::

    $ pyg remove roman
    Uninstalling roman
            /usr/local/lib/python2.7/dist-packages/roman.pyc
            /usr/local/lib/python2.7/dist-packages/roman.py
    Proceed? (y/[n])

If your answer is *yes* the files will be deleted. This operation is **not undoable**::

    $ pyg remove itertools_recipes
    Uninstalling itertools_recipes
            /usr/local/lib/python2.7/dist-packages/itertools_recipes-0.1-py2.7.egg
    Proceed? (y/[n]) y
    Deleting: /usr/local/lib/python2.7/dist-packages/itertools_recipes-0.1-py2.7.egg...
    Removing egg path from easy_install.pth...
    itertools_recipes uninstalled succesfully

.. program:: remove

.. option:: -y, --yes

    Do not ask confirmation of uninstall deletions::

        $ pyg remove -y iterutils
        Uninstalling iterutils
                /usr/local/lib/python2.7/dist-packages/iterutils.py
                /usr/local/lib/python2.7/dist-packages/iterutils-0.1.6.egg-info
                /usr/local/lib/python2.7/dist-packages/iterutils.pyc
        Deleting: /usr/local/lib/python2.7/dist-packages/iterutils.py...
        Deleting: /usr/local/lib/python2.7/dist-packages/iterutils-0.1.6.egg-info...
        Deleting: /usr/local/lib/python2.7/dist-packages/iterutils.pyc...
        Removing egg path from easy_install.pth...
        iterutils uninstalled succesfully

.. option:: -r <path>, --req-file <path>

    Uninstall all the packages listed in the given requirement file.

    ::

        $ echo -e 'itertools_recipes\niterutils' > reqfile.txt
        $ cat reqfile.txt
        itertools_recipes
        iterutils

    ::

        $ pyg remove -r reqfile.txt
        Uninstalling itertools_recipes
                /usr/local/lib/python2.7/dist-packages/itertools_recipes.py
                /usr/local/lib/python2.7/dist-packages/itertools_recipes.pyc
                /usr/local/lib/python2.7/dist-packages/itertools_recipes-0.1.egg-info
        Proceed? (y/[n]) y
        Deleting: /usr/local/lib/python2.7/dist-packages/itertools_recipes.py...
        Deleting: /usr/local/lib/python2.7/dist-packages/itertools_recipes.pyc...
        Deleting: /usr/local/lib/python2.7/dist-packages/itertools_recipes-0.1.egg-info...
        Removing egg path from easy_install.pth...
        itertools_recipes uninstalled succesfully
        Uninstalling iterutils
                /usr/local/lib/python2.7/dist-packages/iterutils.py
                /usr/local/lib/python2.7/dist-packages/iterutils-0.1.6.egg-info
                /usr/local/lib/python2.7/dist-packages/iterutils.pyc
        Proceed? (y/[n]) y
        Deleting: /usr/local/lib/python2.7/dist-packages/iterutils.py...
        Deleting: /usr/local/lib/python2.7/dist-packages/iterutils-0.1.6.egg-info...
        Deleting: /usr/local/lib/python2.7/dist-packages/iterutils.pyc...
        Removing egg path from easy_install.pth...
        iterutils uninstalled succesfully

You can supply both ``packname`` (one or more) and requirement files::

    $ pyg remove -r reqfile.txt docutils
    Uninstalling itertools_recipes
            /usr/local/lib/python2.7/dist-packages/itertools_recipes.py
            /usr/local/lib/python2.7/dist-packages/itertools_recipes.pyc
            /usr/local/lib/python2.7/dist-packages/itertools_recipes-0.1.egg-info
    Proceed? (y/[n]) y
    Deleting: /usr/local/lib/python2.7/dist-packages/itertools_recipes.py
    Deleting: /usr/local/lib/python2.7/dist-packages/itertools_recipes.pyc
    Deleting: /usr/local/lib/python2.7/dist-packages/itertools_recipes-0.1.egg-info
    Removing egg path from easy_install.pth...
    itertools_recipes uninstalled succesfully
    Uninstalling iterutils
            /usr/local/lib/python2.7/dist-packages/iterutils.py
            /usr/local/lib/python2.7/dist-packages/iterutils-0.1.6.egg-info
            /usr/local/lib/python2.7/dist-packages/iterutils.pyc
    Proceed? (y/[n]) y
    Deleting: /usr/local/lib/python2.7/dist-packages/iterutils.py
    Deleting: /usr/local/lib/python2.7/dist-packages/iterutils-0.1.6.egg-info
    Deleting: /usr/local/lib/python2.7/dist-packages/iterutils.pyc
    Removing egg path from easy_install.pth...
    iterutils uninstalled succesfully
    Uninstalling docutils
            /usr/local/lib/python2.7/dist-packages/docutils
            /usr/local/lib/python2.7/dist-packages/docutils-0.7.egg-info
    Proceed? (y/[n]) y
    Deleting: /usr/local/lib/python2.7/dist-packages/docutils
    Deleting: /usr/local/lib/python2.7/dist-packages/docutils-0.7.egg-info
    Removing egg path from easy_install.pth...
    docutils uninstalled succesfully

.. note::

    You can remove Pyg either with ``pyg remove pyg`` or ``pyg remove yourself``!

    .. versionadded:: 0.5