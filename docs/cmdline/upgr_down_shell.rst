Upgrading, downloading and Pyg Shell
====================================

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

.. _shell:

Pyg Shell
---------

.. versionadded:: 0.4

If you need to execute many Pyg commands and you need root privileges (for example on Unix systems), you can fire up Pyg Shell and you are done::

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