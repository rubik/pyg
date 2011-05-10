Pyg and config files
====================

.. versionadded:: 0.4

Config files allow you to override command-line options, and to save them somewhere.
During the initialization process, Pyg looks for configurations file, it this order:

    * :file:`./pyg.conf`: a configuration file in the current working directory:
    * :file:`~/pyg.conf`: where ``~`` stands for your :envvar:`HOME` directory;
    * :file:`~/.pyg/pyg.conf`.

A config file has this structure::

    [section_name]
    option = value

    [section_name2]
    option1 = value1
    option2 = value2
    
    ...


In addition to this, Pyg supports a nonstandard syntax, allowing multiple section names in a single header::

    [section1 & section2 & section6]
    option = value

And it will set that option in all specified sections.

Here is a list of all sections and their options:

    **instal**:

        - *upgrade* = False
        - *upgrade_all* = False
        - *no_deps* = False
        - *index_url* = ``http://pypi.python.org/pypi``
        - *install_dir* = :data:`pyg.locations.INSTALL_DIR`
        - *user* = False
        - *no_scripts* = False
        - *ignore* = False

    **remove**:

        - *yes* = False

    **bundle**:

        - *exclude* = None

    **update**:

        - *yes* = False

    **download**:

        - *unpack* = False
        - *download_dir* = :file:`.`
        - *prefer* = None

    **freeze**:

        - *count* = False
        - *file* = None

    **unlink**:

        - *all* = False