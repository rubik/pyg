Requirement files and bundles
=============================

.. _reqs:

Freezing requirements
---------------------

.. versionchanged:: 0.7
    From Pyg 0.7 onwards, this command has been renamed ``pyg site``.

When you launch::

    $ pyg site

Pyg tries to detect all installed packages and prints requirements on Standard Output::

    # Python version: '2.7.1+ (r271:86832, Apr 11 2011, 18:05:24) \n[GCC 4.5.2]'
    # Python version info: '2.7.1.final.0'
    # Python Prefix: '/usr'
    # Platform: 'linux-i686'
    # Pyg version: '0.6'
    
    Brlapi==0.5.5
    BzrTools==2.3.1
    Cython==0.14.1
    ...
    wadllib==1.1.8
    wsgi-intercept==0.4
    wsgiref==0.1.2
    xkit==0.0.0
    zope.interface==3.6.1

Note that the first lines -- information about the site -- are commented, so that if they're written into a requirement file, they will be ignored.

.. program:: site

.. option:: -f <path>, --file <path>

    Write requirements into the specified file.
    Equivalent to::

        $ pyg site > reqfile.txt

.. option:: -c, --count

    Return the number of installed packages::

        $ pyg site -c
        55

.. option:: -n, --no-info

    Do not add site information::

        $ pyg site -n
        Brlapi==0.5.5
        BzrTools==2.3.1
        Cython==0.14.1
        ...
        wadllib==1.1.8
        wsgi-intercept==0.4
        wsgiref==0.1.2
        xkit==0.0.0
        zope.interface==3.6.1

.. _bundles:

Bundles
-------

.. program:: bundle

The bundle format is specific to Pip (see `Pip documentation <http://www.pip-installer.org/en/latest/index.html#bundles>`_).
To create a bundle do::

    $ pyg bundle app.pyb package_name

This will download all packages (including dependencies) and put them in a bundle file.
Install packages from a bundle is dead simple, and you don't need internet access::

    $ pyg install app.pyb

For example, here is ``Pyg`` bundle::

    $ pyg bundle pyg.pyb pyg
    pyg:
            Retrieving data for pyg [100% - 472.3 Kb / 472.3 Kb]               
            Writing data into pyg-0.6.tar.gz
            pyg downloaded successfully
            Looking for pyg dependencies
                    Found: setuptools
                    Found: pkgtools>=0.4
                    Found: argh>=0.14
    argh>=0.14:
            Retrieving data for argh [100% - 11.4 Kb / 11.4 Kb]             
            Writing data into argh-0.14.0.tar.gz
            argh downloaded successfully
            Looking for argh>=0.14 dependencies
    pkgtools>=0.4:
            Retrieving data for pkgtools [100% - 28.7 Kb / 28.7 Kb]              
            Writing data into pkgtools-0.6.tar.gz
            pkgtools downloaded successfully
            Looking for pkgtools>=0.4 dependencies
    setuptools:
            Retrieving data for setuptools [100% - 250.8 Kb / 250.8 Kb]
            Writing data into setuptools-0.6c11.tar.gz
            setuptools downloaded successfully
            Looking for setuptools dependencies
    Finished processing dependencies
    Adding packages to the bundle
    Adding the manifest file


You can download the generated example bundle :download:`here <>` (direct link to download).

.. option:: -r <path>, --req-file <path>

    .. versionadded:: 0.5

    Specify requirement files containing packages to add. This option can be repeated many times::

        $ pyg bundle bundlename.pybundle -r myreqs.txt -r other_reqs ...

.. option:: -e <requirement>, --exclude <requirement>

    .. versionadded:: 0.5

    Specify packages to exclude from the bundle (can be repeated many times)::

        $ pyg bundle pyg.pyb pyg -e argh -e "pkgtools<=0.3"


.. option:: -d, --use-develop

    .. versionadded:: 0.7

    If specified, for every package look for a local (*develop*) package. If it does not find it, it will download it from PyPI::

        $ pyg bundle pyg pyg -d
        pyg:
                Looking for a local package...
                Looking for pyg dependencies
                        Found: setuptools
                        Found: pkgtools>=0.6.1
                        Found: argh
        argh:
                Looking for a local package...
                Cannot find the location of argh
                Retrieving data for argh [100% - 11.4 Kb / 11.4 Kb]             
                Writing data into argh-0.14.0.tar.gz
                argh downloaded successfully
                Looking for argh dependencies
        pkgtools>=0.6.1:
                Looking for a local package...
                Looking for pkgtools>=0.6.1 dependencies
        setuptools:
                Looking for a local package...
                Cannot find the location of setuptools
                Retrieving data for setuptools [100% - 250.8 Kb / 250.8 Kb] 
                Writing data into setuptools-0.6c11.tar.gz
                setuptools downloaded successfully
                Looking for setuptools dependencies
        Finished processing dependencies
        Adding packages to the bundle
        Adding the manifest file


.. _pack_doc:

Packs
-----

.. program:: pack

.. versionadded:: 0.7

Packs are zip files containing an egg (which includes all necessary packages) and some Python executable files (:file:`run_\{name\}.py`).
The :command:`pack` command has the following syntax::

    pyg pack {packname} {package} [{options}, ...]

Its name can either have the ``.zip`` extension or not, and can be a path.

You can create a pack with the following command::

    $ pyg pack pyg.zip pyg
    Generating the bundle...
    pyg:
            Retrieving data for pyg [100% - 472.3 Kb / 472.3 Kb]               
            Writing data into pyg-0.6.tar.gz
            pyg downloaded successfully
            Looking for pyg dependencies
                    Found: setuptools
                    Found: pkgtools>=0.4
                    Found: argh>=0.14
    argh>=0.14:
            Retrieving data for argh [100% - 11.4 Kb / 11.4 Kb]             
            Writing data into argh-0.14.0.tar.gz
            argh downloaded successfully
            Looking for argh>=0.14 dependencies
    pkgtools>=0.4:
            Retrieving data for pkgtools [100% - 27.2 Kb / 27.2 Kb]              
            Writing data into pkgtools-0.6.1.tar.gz
            pkgtools downloaded successfully
            Looking for pkgtools>=0.4 dependencies
    setuptools:
            Retrieving data for setuptools [100% - 250.8 Kb / 250.8 Kb] 
            Writing data into setuptools-0.6c11.tar.gz
            setuptools downloaded successfully
            Looking for setuptools dependencies
    Finished processing dependencies
    Adding packages to the bundle
    Generating EGG-INFO...


For example, Pyg Pack has the following structure::

    pyg-0.6
        ├── pyg.egg
        ├── run_easy_install-2.3.py
        ├── run_easy_install.py
        └── run_pyg.py

As you can see, there are already some executable files (Pyg looks for them in the packages' :file:`entry_points.txt` file) and you can run them without installing Pyg: everything necessary is in :file:`pyg.egg`.
Amazing!

If you want to try it, download it :download:`here <>` (direct link to download), unpack it and run the :file:`run_pyg.py` file. You will be able to use Pyg without installing it!

.. option:: -e <requirement>, --exclude <requirement>

    Specify packages to exclude from the pack (can be repeated many times)::

        $ pyg pack pyg.zip pyg -e argh -e "pkgtools<=0.3"

    .. warning::
        If you exclude some packages from the pack it is very likely that its executables will not work, without some dependencies.

.. option:: -d, --use-develop

    If specified, for every package look for a local (*develop*) distribution. If it does not find it, it will download it from PyPI.

    On certain systems (probably Unix-like ones) the :command:`pack` command with this option enabled may require root privileges, because Pyg will run the :command:`sdist` command (``python setup.py sdist``) for every local distribution.

    (See also :option:`bundle -d`.)