Using Pyg from the command line
===============================

Pyg should be used mostly from the command line, as it requires root's privileges to install and remove packages.

On some systems (e.g. on \*nix systems), you may need root privileges to execute some commands such as :command:`install`, :command:`uninstall`, 

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

Pyg supports these files:

    * :file:`.tar.gz`
    * :file:`.tar.bz2`
    * :file:`.zip`
    * :file:`.egg`
    * :file:`.pybundle`
    * :file:`.pyb` (an abbreviation of Pip's bundle files)

.. option:: -e <URL>, --editable <URL>

    Install a package in editable mode (``python setup.py develop``) from an online repository. Supported VCS are:

        * Git (prefix ``git+``)
        * Mercurial (prefix ``hg+``)
        * Bazaar (prefix ``bzr+``)
        * Subversion (prefix ``svn+``)

    The URL syntax is as follow::

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
    For example, you install ``pypol_`` v0.4::

        $ pyg install pypol_==0.4
        Best match: pypol_==0.4
        Downloading pypol_
        Checking md5 sum
        Running setup.py egg_info for pypol_
        Running setup.py install for pypol_
        pypol_ installed successfully

    Later you may want to re-install the package. Instead of running ``uninstall`` and then ``install``, you can use the :option:`-U` option::

        $ pyg install -U pypol_
        Best match: pypol_==0.5
        Downloading pypol_
        Checking md5 sum
        Installing pypol_ egg file
        pypol_ installed successfully

    .. versionadded:: 0.2

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

Removing a package is dead simple::

    $ pyg uninstall packname

Pyg tries to detect the package's folder and delete it::

    $ pyg uninstall sphinx
    Uninstalling sphinx
            /usr/bin/sphinx-build
            /usr/local/lib/python2.7/dist-packages/Sphinx-1.0.7-py2.7.egg
            /usr/bin/sphinx-quickstart
            /usr/bin/sphinx-autogen
    Proceed? (y/[n]) 


If *packname* is a module and not a package, Pyg will automatically detect it::

    $ pyg uninstall roman
    Uninstalling roman
            /usr/local/lib/python2.7/dist-packages/roman.pyc
            /usr/local/lib/python2.7/dist-packages/roman.py
    Proceed? (y/[n])

If your answer is *yes* the files will be deleted. This operation is **not undoable**::

    $ pyg uninstall itertools_recipes
    Uninstalling itertools_recipes
            /usr/local/lib/python2.7/dist-packages/itertools_recipes-0.1-py2.7.egg
    Proceed? (y/[n]) y
    Deleting: /usr/local/lib/python2.7/dist-packages/itertools_recipes-0.1-py2.7.egg...
    Removing egg path from easy_install.pth...
    itertools_recipes uninstalled succesfully

.. program:: uninstall

.. option:: -y, --yes

    Do not ask confirmation of uninstall deletions::

        $ pyg uninstall -y iterutils
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

        $ pyg uninstall -r reqfile.txt
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

    $ pyg uninstall -r reqfile.txt docutils
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


The ``rm`` command
------------------

Since package uninstallation is very common the ``rm`` command is an alias for the :ref:`uninstall <uninst>` command::

    $ sudo pyg rm sphinx
    Uninstalling sphinx
            /usr/bin/sphinx-build
            /usr/local/lib/python2.7/dist-packages/Sphinx-1.0.7-py2.7.egg
            /usr/bin/sphinx-quickstart
            /usr/bin/sphinx-autogen
    Proceed? (y/[n]) 
    sphinx has not been uninstalled


.. _reqs:

Freezing requirements
---------------------

When you launch::

    $ pyg freeze

Pyg tries to detect all installed packages and prints requirements on Standard Output::

    BeautifulSoup==3.2.0
    BzrTools==2.3.1
    Fabric==0.9.3
    Jinja2==2.5.5
    Logbook==0.3
    Mako==0.3.6
    MarkupSafe==0.9.2
    PAM==0.4.2
    Pygments==1.4
    SQLAlchemy==0.6.4
    Sphinx==1.0.7
    ...
    pytz==2010b
    simplejson==2.1.2
    system_service==0.1.6
    ubuntu_dev_tools==0.120
    ufw==0.30.0_3ubuntu1
    unattended_upgrades==0.1
    urllib3==0.3.1
    wadllib==1.1.8
    wsgi_intercept==0.4
    xkit==0.0.0
    zope.interface==3.6.1

.. program:: freeze

.. option:: -f <path>, --file <path>

    Write requirements into the specified file.
    Equivalent to::

        $ pyg freeze > reqfile.txt

.. option:: -c, --count

    Return the number of installed packages::

        $ pyg freeze -c
        55


Linking directories
-------------------

If you want to add a directory to :envvar:`PYTHONPATH` permanently the ``link`` command is what you need::

    $ pyg link dirname

When you link a directory Pyg add in a :file:`.pth` file the dir's path.


Unlinking
---------

.. program:: unlink

If you want to remove a directory from :envvar:`PYTHONPATH` you can use the ``unlink`` command.
Pyg can remove a directory from :envvar:`PYTHONPATH` only if that directory has been added previously.

.. option:: -a, --all

    Remove all links in the :file:`.pth` file.


The ``list`` command
--------------------

You can use this command to list all package's avaiable versions::

    $ pyg list pypol_
    0.5	installed
    0.4
    0.3
    0.2

    $ pyg list itertools_recipes
    0.1

If that package is installed, Pyg will add ``installed`` after the current version.


Searching PyPI
--------------

Pyg can perform searches on PyPI with the ``search`` command::

    $ pyg search pypol_
    pypol_  0.5 - Python polynomial library
    pypolkit  0.1 - Python bindings for polkit-grant

    $ pyg search distribute
    distribute  0.6.15 - Easily download, build, install, upgrade, and uninstall Python packages
    virtualenv-distribute  1.3.4.4 - Virtual Python Environment builder


Checking installed packages
---------------------------

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


Downloading packages
--------------------

.. versionadded:: 0.2

If you only need to download a package you can use the ``download`` command::

    $ pyg download packname

If the requirement is not satisfied Pyg won't download anything::

    $ pyg download pyg==1024
    E: Did not find files to download

.. program:: download

.. option:: -u, --unpack

    After downloading a package, Pyg unpacks it::

        $ pyg download -u pypol_
        Found egg file for another Python version: 2.6. Continue searching...
        Retrieving data for pypol_
        Writing data into pypol_-0.5-py2.7.egg
        pypol_ downloaded successfully
        Unpacking pypol_-0.5-py2.7.egg to ./pypol_-0.5-py2.7
        $ l
        pypol_-0.5-py2.7/  pypol_-0.5-py2.7.egg

.. option:: -d <path>, --download-dir <path>

    Where to download the package, default to :file:`.` (current working directory)::

        $ pyg download -d /downloads/python_downloads/ pyg

    If the path does not exist, Pyg will create it.

.. option:: -p <ext>, --prefer <ext>

    The preferred file type for the download. Pyg looks for that file type and, if it does not exists, will try another extension::

        $ pyg download -p .tar.gz pyg
        Retrieving data for pyg
        Writing data into pyg-0.1.tar.gz
        pyg downloaded successfully

        $ pyg download -p .egg pyg
        Retrieving data for pyg
        Writing data into pyg-0.1-py2.7.egg
        pyg downloaded successfully

        $ pyg download -p .myawesomeext pyg
        Retrieving data for pyg
        Writing data into pyg-0.1-py2.7.egg
        pyg downloaded successfully


.. _upd:

Upgrading installed packages
----------------------------

.. versionadded:: 0.3

.. program:: update

When you use the ``update`` command, Pyg searches through all installed packages and checks for updates. If there are some, Pyg installs them.

Before loading the entire list of installed packages, Pyg checks the :file:`~/.pyg/installed_packages.txt` file. If it exists Pyg will update only packages in that file::

    $ pyg update
    Cache file not found: $HOME/.pyg/installed_packages.txt
    Loading list of installed packages...
    15 packages loaded
    Searching for updates
    A new release is avaiable for simplejson: 2.1.5 (old 2.1.3)
    Do you want to upgrade? (y/[n]) y
    Upgrading simplejson to 2.1.5
            Installing simplejson-2.1.5.tar.gz...
                Installing simplejson-2.1.5.tar.gz
                Running setup.py egg_info for simplejson
                Running setup.py install for simplejson
                simplejson installed successfully

    ...

    Updating finished successfully

    $ pyg update
    Loading list of installed packages...
    Reading cache...
    15 packages loaded
    Searching for updates
    A new release is avaiable for wadllib: 1.2.0 (old 1.1.8)
    Do you want to upgrade? (y/[n]) n
    wadllib has not been upgraded
    A new release is avaiable for launchpadlib: 1.9.8 (old 1.9.7)
    Do you want to upgrade? (y/[n]) n
    launchpadlib has not been upgraded
    Updating finished successfully

.. _shell:

Pyg Shell
---------

.. versionadded:: 0.4

If you need to execute many Pyg commands and you need root privileges (for example on *\*nix* systems), you can fire up Pyg Shell and you are done::

    $ pyg shell

Now you can use all Pyg's commands plus 3 shell commands: :command:`cd`, :command:`pwd`, and :command:`ls`::

    pyg:/home/user$ check pyg
    True
    pyg:/home/user$ check pyg==0.3.2
    True
    pyg:/home/user$ ls
    pkgtools  pyg
    pyg:/home/user$ pwd
    /home/user
    pyg:/home/user$ cd pyg
    pyg:/home/user/pyg$ pwd
    /home/user/pyg
    pyg:/home/user/pyg$ install sphinx
    sphinx is already installed
    pyg:/home/user/pyg$ install -U sphinx
    sphinx is already installed, upgrading...
    Looking for sphinx releases on PyPI
    Best match: Sphinx==1.0.7
    Downloading Sphinx
    Checking md5 sum
    Running setup.py egg_info for Sphinx
    Running setup.py install for Sphinx
    Installing dependencies...
        Jinja2>=2.2 is already installed
        docutils>=0.5 is already installed
        Pygments>=0.8 is already installed
    Finished installing dependencies
    Sphinx installed successfully
    pyg:/home/user/pyg$ cd
    pyg:/home/user$ exit


.. _bundles:

Bundles
-------

The bundle format is specific to Pip (see `Pip documentation <http://www.pip-installer.org/en/latest/index.html#bundles>`_).
To create a bundle do::

    $ pyg bundle app.pyb package_name

This will download all packages (including dependencies) and put them in a bundle file.
Install packages from a bundle is dead simple, and you don't need internet access::

    $ pyg install app.pyb

For example, here is ``Pyg`` bundle::

    $ pyg bundle pyg.pyb pyg==0.4
    pyg==0.4:
            Retrieving data for pyg
            Writing data into pyg-0.4.tar.gz
            pyg downloaded successfully
            Looking for pyg dependencies
                    Found: setuptools
                    Found: pkgtools>=0.3.1
                    Found: argh>=0.14
    argh>=0.14:
            Retrieving data for argh
            Writing data into argh-0.14.0.tar.gz
            argh downloaded successfully
            Looking for argh>=0.14 dependencies
    pkgtools>=0.3.1:
            Retrieving data for pkgtools
            Writing data into pkgtools-0.3.1.tar.gz
            pkgtools downloaded successfully
            Looking for pkgtools>=0.3.1 dependencies
    setuptools:
            Retrieving data for setuptools
            Writing data into setuptools-0.6c11.tar.gz
            setuptools downloaded successfully
            Looking for setuptools dependencies
    Finished processing dependencies
    Adding packages to the bundle
    Adding the manifest file


You can download the generated bundle :download:`here <../../pyg.pyb>` (direct link to download).