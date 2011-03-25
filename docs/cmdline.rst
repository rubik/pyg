.. _cmdline:

Using Pyg from the command line
===============================

Pyg should be used mostly from the command line, as it requires root's privileges to install and remove packages.

Installing
----------

To install a package, simply run::

    $ pyg install packname

where *packname* is the name of the package you want to install.

.. program:: install

.. option:: -r <path>, --req-file <path>

    Install packages from the specified requirement file::

        $ pyg install -r requirements.txt

    See also: :ref:`reqs`

.. option:: -f <path>, --file <path>

    Do not download the package, but use the one specified::

        $ pyg install -f Sphinx-1.0.7.tar.gz

    The path can be absolute::

        $ pyg install -f /home/42/Sphinx-1.0.7-py2.7.egg

    Supported files:

    * :file:`.tar.gz`
    * :file:`.tar.bz2`
    * :file:`.zip`
    * :file:`.egg`
    * :file:`.pybundle`
    * :file:`.pyb` (an abbreviation of pip's bundle files)

.. option:: -u, --upgrade

    If the package is already installed, install it again.
    For example, if you install ``pypol_`` v0.4::

        $ pyg install pypol_==0.4
        Best match: pypol_==0.4
        Downloading pypol_
        Checking md5 sum
        Running setup.py egg_info for pypol_
        Running setup.py install for pypol_
        pypol_ installed successfully

    And then run ``list``::

        $ pyg list pypol_
        0.5
        0.4	installed
        0.3
        0.2

    You may want to re-install the package. Instead of running ``uninstall`` and then ``install``, you can use the :option:`-u` option::

        $ pyg install -u pypol_
        Best match: pypol_==0.5
        Downloading pypol_
        Checking md5 sum
        Installing pypol_ egg file
        pypol_ installed successfully

    And now::

        $ pyg list pypol_
        0.5	installed
        0.4
        0.3
        0.2

.. option:: -n, --no-deps

    Do not install package's dependencies.

    TODO: ADD EXAMPLE

.. option:: -i <url>, --index-url <url>

    Specify the base URL of Python Package Index (default to ``http://pypi.python.org/pypi``).

    TODO: ADD EXAMPLE

.. option:: --user

    Install the package in the user site-packages.

    TODO: ADD EXAMPLE

.. option:: -d, --develop

    Install the package in development mode.

    .. warning::

        Not Implemented Yet


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

    Do not ask confirmation of uninstall deletions.

    TODO: ADD EXAMPLE

.. option:: -r <path>, --req-file <path>

    Uninstall all the packages listed in the given requirement file.

    TODO: ADD EXAMPLE


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

If you want to add a directory to :envvar:`PYTHONPATH` permanently the ``link`` command is what do you need::

    $ pyg link dirname

When you link a directory Pyg add in a :file:`.pth` file the dir's path.

TODO: ADD EXAMPLE


Unlinking
---------

If you want to remove a directory from :envvar:`PYTHONPATH` you can use the ``unlink`` command.
Pyg can remove a directory from :envvar:`PYTHONPATH` only if that directory has been added previously.

.. program:: unlink

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


Downloading packages
--------------------

If you only need to download a package you can use the ``download`` command::

    $ pyg download packname

If the requirement is not satisfied Pyg won't download anything::

    $ pyg download pyg==1024
    E: Did not find files to download

.. program:: download

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
