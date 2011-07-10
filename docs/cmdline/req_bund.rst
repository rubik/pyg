Requirement files and bundles
=============================

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


You can download the generated example bundle :download:`here <../files/pyg.pyb>` (direct link to download).

.. option:: -r <path>, --req-file <path>

    Specify requirement files containing packages to add. This option can be repeated many times::

        $ pyg bundle bundlename.pybundle -r myreqs.txt -r other_reqs ...

    .. versionadded:: 0.5

.. option:: -e <requirement>, --exclude <requirement>

    Specify packages to exclude from the bundle (can be repeated many times)::

        $ pyg bundle pyg.pyb pyg -e argh -e pkgtools<=0.3

    .. versionadded:: 0.5


Packs
-----

.. program:: pack

.. versionadded:: 0.7

Packs are zip files containing an egg (which includes all necessary packages) and a Python executable file (:file:`run.py`).
You can create a pack with the following command::

    TODO